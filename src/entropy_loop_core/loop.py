"""The core failure-compiling loop.

:class:`EntropyLoop` is the orchestrator of the *Failure Compiler*. For each
attempt it runs an agent, verifies the output, and — on failure — records a
structured trace, compiles a lesson, generates a regression case, and retries
with the accumulated lessons in context. The agent is any callable that turns
an :class:`~entropy_loop_core.types.AgentContext` into output, so the loop stays
agnostic to how outputs are actually produced.
"""

from __future__ import annotations

from collections.abc import Callable

from .lessons import LessonGenerator
from .memory import MemoryStore
from .regression import RegressionGenerator
from .types import (
    AgentContext,
    AgentOutput,
    FailureTrace,
    LoopResult,
    LoopStatus,
    Severity,
    Task,
    VerificationResult,
)
from .verification import Verifier

# An agent turns an attempt context into output. It may return an AgentOutput
# or a plain string, which the loop wraps automatically.
Agent = Callable[[AgentContext], "AgentOutput | str"]


class EntropyLoop:
    """Runs a task with verification, failure memory, lessons, and retries.

    On each attempt the loop builds an :class:`AgentContext` (carrying the
    lessons relevant to the task so far), invokes the agent, and verifies the
    output. On success it returns; on failure it records a
    :class:`~entropy_loop_core.types.FailureTrace`, compiles a
    :class:`~entropy_loop_core.types.Lesson`, optionally generates a
    :class:`~entropy_loop_core.types.RegressionCase`, and retries.
    """

    def __init__(
        self,
        verifier: Verifier,
        memory: MemoryStore,
        lesson_generator: LessonGenerator | None = None,
        regression_generator: RegressionGenerator | None = None,
        max_attempts: int = 3,
        generate_regressions: bool = True,
    ) -> None:
        """Create an entropy loop.

        Args:
            verifier: Validates each agent output.
            memory: Store that accumulates failures and lessons across attempts.
            lesson_generator: Compiles failures into lessons; a default
                :class:`LessonGenerator` is used when omitted.
            regression_generator: Builds regression cases; a default
                :class:`RegressionGenerator` is used when omitted.
            max_attempts: Maximum number of attempts before giving up (>= 1).
            generate_regressions: Whether to generate a regression case per
                failure.

        Raises:
            ValueError: If ``max_attempts`` is less than 1.
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._verifier = verifier
        self._memory = memory
        self._lesson_generator = lesson_generator or LessonGenerator()
        self._regression_generator = regression_generator or RegressionGenerator()
        self._max_attempts = max_attempts
        self._generate_regressions = generate_regressions

    def run(self, task: Task, agent: Agent) -> LoopResult:
        """Run ``task`` through ``agent`` until it verifies or attempts run out.

        Args:
            task: The task to execute.
            agent: Callable invoked as ``agent(context)`` returning output.

        Returns:
            A :class:`LoopResult` capturing the final status, attempt count,
            output, and the failures, lessons, and regression cases produced.
        """
        failures: list[FailureTrace] = []
        lessons = []
        regressions = []

        for attempt in range(1, self._max_attempts + 1):
            context = AgentContext(
                task=task,
                attempt=attempt,
                lessons=self._memory.relevant_lessons(task),
            )
            output, trace = self._attempt(agent, context)

            if trace is None:
                return LoopResult(
                    status=LoopStatus.SUCCESS,
                    attempts=attempt,
                    output=output,
                    failures=failures,
                    lessons=lessons,
                    regression_cases=regressions,
                )

            # Compile the failure into durable, reusable artifacts.
            self._memory.add_failure(trace)
            failures.append(trace)

            lesson = self._lesson_generator.generate(trace)
            self._memory.add_lesson(lesson)
            lessons.append(lesson)

            if self._generate_regressions:
                regressions.append(self._regression_generator.generate(trace))

        return LoopResult(
            status=LoopStatus.FAILED,
            attempts=self._max_attempts,
            output=None,
            failures=failures,
            lessons=lessons,
            regression_cases=regressions,
        )

    def _attempt(
        self, agent: Agent, context: AgentContext
    ) -> tuple[AgentOutput | None, FailureTrace | None]:
        """Run a single attempt.

        Returns an ``(output, trace)`` pair. Exactly one side is populated:
        ``trace`` is ``None`` on success, otherwise ``output`` is ``None``.
        """
        task, attempt = context.task, context.attempt
        try:
            raw = agent(context)
        except Exception as exc:  # noqa: BLE001 - surface any agent error as failure
            result = VerificationResult(
                passed=False,
                reason=f"agent raised {type(exc).__name__}: {exc}",
                rule_name="agent_exception",
                severity=Severity.CRITICAL,
            )
            trace = FailureTrace(
                task=task,
                output=AgentOutput(content=""),
                verification_result=result,
                attempt=attempt,
            )
            return None, trace

        output = raw if isinstance(raw, AgentOutput) else AgentOutput(content=str(raw))
        result = self._verifier.verify(task, output)
        if result.passed:
            return output, None

        trace = FailureTrace(
            task=task,
            output=output,
            verification_result=result,
            attempt=attempt,
        )
        return None, trace
