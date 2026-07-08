"""Replaying regression cases.

Where v0.2.0 *generated* regression cases from failures, :class:`RegressionRunner`
*replays* them: it turns each :class:`~entropy_loop_core.types.RegressionCase`
back into a task, runs an agent once, verifies the output, and reports whether
the case now passes. This is how a remembered failure becomes a repeatable check
— replay it before the same agent bug ships again.

The runner is deterministic and does no I/O — no retries, no async, no network,
no external API calls. Agent exceptions are caught and reported as failures.
"""

from __future__ import annotations

from .loop import Agent
from .types import (
    AgentOutput,
    RegressionCase,
    RegressionReport,
    RegressionRunResult,
    RegressionSuite,
    RetryContext,
    Task,
)
from .verification import Verifier


class RegressionRunner:
    """Replays regression cases through an agent and verifier.

    The runner does not retry: each case is run exactly once (attempt 1, no
    lessons), verified, and reported. Use it to check whether a past failure is
    fixed by the current agent.
    """

    def run_case(
        self, case: RegressionCase, agent: Agent, verifier: Verifier
    ) -> RegressionRunResult:
        """Replay a single regression case.

        Args:
            case: The regression case to replay.
            agent: Callable invoked as ``agent(task, retry_context)``.
            verifier: The verifier that decides pass/fail.

        Returns:
            A :class:`RegressionRunResult` capturing pass/fail, the output, and
            the verification verdict (or an error if the agent raised).
        """
        task = Task(id=case.name, instruction=case.instruction)
        context = RetryContext(attempt=1)
        try:
            raw = agent(task, context)
        except Exception as exc:  # noqa: BLE001 - report any agent error as failure
            return RegressionRunResult(
                case=case,
                passed=False,
                error=f"agent raised {type(exc).__name__}: {exc}",
            )

        output = raw if isinstance(raw, AgentOutput) else AgentOutput(content=str(raw))
        result = verifier.verify(output)
        return RegressionRunResult(
            case=case,
            passed=result.passed,
            output=output,
            verification_result=result,
        )

    def run_suite(
        self, suite: RegressionSuite, agent: Agent, verifier: Verifier
    ) -> RegressionReport:
        """Replay every case in a suite and summarize the outcome.

        Args:
            suite: The regression suite to replay.
            agent: Callable invoked as ``agent(task, retry_context)``.
            verifier: The verifier that decides pass/fail for each case.

        Returns:
            A :class:`RegressionReport` with per-case results and totals.
        """
        results = [self.run_case(case, agent, verifier) for case in suite.cases]
        passed = sum(1 for result in results if result.passed)
        return RegressionReport(
            suite_name=suite.name,
            total_cases=len(results),
            passed=passed,
            failed=len(results) - passed,
            results=results,
        )
