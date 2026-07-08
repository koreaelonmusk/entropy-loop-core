"""Guard an agent that must return JSON, then replay the failure as a regression.

Run it with::

    python examples/json_agent_guard.py

A universal LLM pain: an agent is supposed to return JSON but emits something
that does not parse. This example captures that failure, turns it into a
regression case, and then *replays* the case against a corrected agent to check
that the same bug no longer ships.

No real LLM, no API keys, no network — just the deterministic core.
"""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    RegressionRunner,
    RegressionSuite,
    RetryContext,
    Task,
    Verifier,
    export_regression_report,
    generate_regression_case,
)


def main() -> None:
    """Capture a broken-JSON failure, then replay it against a fixed agent."""
    task = Task(id="json-001", instruction="return the user record as JSON")
    verifier = Verifier().require_non_empty().expect_json()

    # 1. The original agent returned malformed JSON.
    broken_output = AgentOutput(content="{ name: 'ada', admin: true ")
    result = verifier.verify(broken_output)
    print(f"original output failed verification: {result.reason}")

    # 2. Compile that failure into a regression case and a suite.
    trace = FailureTrace(
        task=task,
        output=broken_output,
        verification_result=result,
        attempt=1,
    )
    case = generate_regression_case(trace)
    suite = RegressionSuite(name="json-agent-guard", cases=[case])
    print(f"regression case: {case.name} (category={case.category})")

    # 3. A corrected agent now returns valid JSON. Replay the suite against it.
    def fixed_agent(task: Task, context: RetryContext) -> AgentOutput:
        return AgentOutput(content='{"name": "ada", "admin": true}')

    report = RegressionRunner().run_suite(suite, fixed_agent, verifier)

    print("\nreplay report:")
    print(f"  {export_regression_report(report)}")
    print(f"\nsame bug shipped again? {'NO' if report.failed == 0 else 'YES'}")


if __name__ == "__main__":
    main()
