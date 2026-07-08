"""The core failure-compiling loop.

:class:`EntropyLoop` is the orchestrator of the *Failure Compiler*. For each
attempt it builds a :class:`~entropy_loop_core.types.RetryContext`, runs an
agent, and verifies the output. On failure it records a structured trace,
compiles a lesson, remembers both, and retries with the accumulated context.

The agent is any callable ``(task, retry_context) -> AgentOutput | str``, so the
loop stays agnostic to how outputs are actually produced. It is synchronous,
has no plugin system, and executes no tools or nested agents — one clear loop.
"""

from __future__ import annotations

from collections.abc import Callable

from .lessons import LessonGenerator
from .memory import MemoryStore
from .types import (
    AgentOutput,
    FailureTrace,
    Lesson,
    LoopResult,
    RetryContext,
    Task,
    VerificationResult,
)
from .verification import Verifier

# An agent turns a task and its retry context into output. It may return an
# AgentOutput or a plain string, which the loop wraps automatically.
Agent = Callable[[Task, RetryContext], "AgentOutput | str"]


class EntropyLoop:
    """Runs a task with verification, failure memory, lessons, and retries.

    On each attempt the loop builds a :class:`RetryContext` (carrying prior
    failures and the lessons relevant to the task), invokes the agent, and
    verifies the output. On success it returns; on failure it records a
    :class:`~entropy_loop_core.types.FailureTrace`, compiles a
    :class:`~entropy_loop_core.types.Lesson`, remembers both, and retries.
    """

    def __init__(
        self,
        verifier: Verifier,
        memory: MemoryStore,
        lesson_generator: LessonGenerator | None = None,
        max_attempts: int = 3,
    ) -> None:
        """Create an entropy loop.

        Args:
            verifier: Validates each agent output.
            memory: Store that accumulates failures and lessons across attempts.
            lesson_generator: Compiles failures into lessons; a default
                :class:`LessonGenerator` is used when omitted.
            max_attempts: Maximum number of attempts before giving up (>= 1).

        Raises:
            ValueError: If ``max_attempts`` is less than 1.
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._verifier = verifier
        self._memory = memory
        self._lesson_generator = lesson_generator or LessonGenerator()
        self._max_attempts = max_attempts

    def run(self, task: Task, agent: Agent) -> LoopResult:
        """Run ``task`` through ``agent`` until it verifies or attempts run out.

        Args:
            task: The task to execute.
            agent: Callable invoked as ``agent(task, retry_context)``.

        Returns:
            A :class:`LoopResult` capturing the final status, attempt count,
            output, and the failures, lessons, and errors produced.
        """
        failures: list[FailureTrace] = []
        lessons: list[Lesson] = []
        errors: list[str] = []

        for attempt in range(1, self._max_attempts + 1):
            context = RetryContext(
                attempt=attempt,
                prior_failures=list(failures),
                lessons=self._memory.relevant_lessons(task),
            )
            output, trace = self._attempt(task, agent, context)

            if trace is None:
                return LoopResult(
                    status="success",
                    attempts=attempt,
                    output=output,
                    failures=failures,
                    lessons=lessons,
                    errors=errors,
                )

            # Compile the failure into durable, reusable artifacts.
            self._memory.add_failure(trace)
            failures.append(trace)
            errors.append(trace.verification_result.reason)

            lesson = self._lesson_generator.generate(trace)
            self._memory.add_lesson(lesson)
            lessons.append(lesson)

        return LoopResult(
            status="failed",
            attempts=self._max_attempts,
            output=None,
            failures=failures,
            lessons=lessons,
            errors=errors,
        )

    def _attempt(
        self, task: Task, agent: Agent, context: RetryContext
    ) -> tuple[AgentOutput | None, FailureTrace | None]:
        """Run a single attempt.

        Returns an ``(output, trace)`` pair. Exactly one side is populated:
        ``trace`` is ``None`` on success, otherwise ``output`` is ``None``.
        """
        try:
            raw = agent(task, context)
        except Exception as exc:  # noqa: BLE001 - surface any agent error as failure
            result = VerificationResult(
                passed=False,
                reason=f"agent raised {type(exc).__name__}: {exc}",
                rule_name="agent_exception",
                severity="critical",
            )
            trace = FailureTrace(
                task=task,
                output=AgentOutput(content=""),
                verification_result=result,
                attempt=context.attempt,
            )
            return None, trace

        output = raw if isinstance(raw, AgentOutput) else AgentOutput(content=str(raw))
        result = self._verifier.verify(output)
        if result.passed:
            return output, None

        trace = FailureTrace(
            task=task,
            output=output,
            verification_result=result,
            attempt=context.attempt,
        )
        return None, trace
