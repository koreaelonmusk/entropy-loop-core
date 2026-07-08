"""The core retry-with-memory loop.

:class:`EntropyLoop` ties the pieces together: it runs an agent, verifies the
output, records any failure to memory, and retries up to a bound. The agent is
any callable that turns a :class:`Task` into a string, so the loop stays
agnostic to how outputs are actually produced.
"""

from __future__ import annotations

from collections.abc import Callable

from .memory import MemoryStore
from .types import Failure, LoopResult, LoopStatus, Task
from .verification import Verifier

# An agent turns a task into an output string. It receives the attempt number
# (1-based) so it can adapt behaviour across retries.
Agent = Callable[[Task, int], str]


class EntropyLoop:
    """Runs a task with verification, failure memory, and retries.

    On each attempt the loop invokes the agent, verifies the output, and either
    returns success or records the failure and retries. Failures are persisted
    to the supplied :class:`MemoryStore` so callers can inspect what went wrong.
    """

    def __init__(
        self,
        verifier: Verifier,
        memory: MemoryStore,
        max_attempts: int = 3,
    ) -> None:
        """Create an entropy loop.

        Args:
            verifier: Validates each agent output.
            memory: Store that accumulates failures across attempts.
            max_attempts: Maximum number of attempts before giving up. Must be
                at least 1.

        Raises:
            ValueError: If ``max_attempts`` is less than 1.
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._verifier = verifier
        self._memory = memory
        self._max_attempts = max_attempts

    def run(self, task: Task, agent: Agent) -> LoopResult:
        """Run ``task`` through ``agent`` until it verifies or attempts run out.

        Args:
            task: The task to execute.
            agent: Callable invoked as ``agent(task, attempt)`` returning output.

        Returns:
            A :class:`LoopResult` capturing the final status, attempt count,
            output, and the ordered list of errors encountered.
        """
        errors: list[str] = []

        for attempt in range(1, self._max_attempts + 1):
            output, error = self._attempt(task, agent, attempt)
            if error is None:
                return LoopResult(
                    status=LoopStatus.SUCCESS,
                    attempts=attempt,
                    output=output,
                    errors=errors,
                )

            errors.append(error)
            self._memory.record_failure(
                Failure(task_prompt=task.prompt, attempt=attempt, reason=error)
            )

        return LoopResult(
            status=LoopStatus.FAILED,
            attempts=self._max_attempts,
            output=None,
            errors=errors,
        )

    def _attempt(
        self, task: Task, agent: Agent, attempt: int
    ) -> tuple[str | None, str | None]:
        """Run a single attempt.

        Returns a ``(output, error)`` pair. Exactly one side is populated:
        ``error`` is ``None`` on success, otherwise ``output`` is ``None``.
        """
        try:
            output = agent(task, attempt)
        except Exception as exc:  # noqa: BLE001 - surface any agent error as a failure
            return None, f"agent raised {type(exc).__name__}: {exc}"

        result = self._verifier.verify(output)
        if not result.ok:
            return None, result.error
        return output, None
