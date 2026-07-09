"""Build a regression pack for a JSON agent, save it, run it, and write a report.

Run it with::

    python examples/regression_pack_ci.py

This produces `examples/json_agent_guard.pack.json` — a portable, inspectable
regression pack you can commit and run in CI with::

    entropy-loop run-pack examples/json_agent_guard.pack.json

`run-pack` exits non-zero if a known agent regression reappears, which is what
turns replayable failures into a CI gate. Deterministic: no LLM, no network.
"""

from __future__ import annotations

from pathlib import Path

from entropy_loop_core import (
    RegressionCase,
    RegressionPack,
    RegressionPackRunner,
    VerificationPolicy,
    save_regression_pack,
    write_json_report,
)

PACK_PATH = Path(__file__).parent / "json_agent_guard.pack.json"


def build_pack() -> RegressionPack:
    """A pack of JSON-output cases with reference outputs that should pass."""
    policy = VerificationPolicy(require_non_empty=True, expect_json=True)
    cases = [
        RegressionCase(
            name="json-1",
            instruction="return the user record as JSON",
            expected_rule="valid_json_when_expected",
            failure_reason="expected valid JSON",
            category="invalid_json",
        ),
        RegressionCase(
            name="json-2",
            instruction="return the order as JSON",
            expected_rule="valid_json_when_expected",
            failure_reason="expected valid JSON",
            category="invalid_json",
        ),
        RegressionCase(
            name="json-3",
            instruction="return the status as JSON",
            expected_rule="valid_json_when_expected",
            failure_reason="expected valid JSON",
            category="invalid_json",
        ),
    ]
    outputs = {
        "json-1": '{"user": "ada"}',
        "json-2": '{"order": 42}',
        "json-3": '{"status": "ok"}',
    }
    return RegressionPack(
        name="json-agent-guard", policy=policy, cases=cases, outputs=outputs
    )


def main() -> None:
    """Save the pack, run it, and write a JSON report."""
    pack = build_pack()
    save_regression_pack(pack, PACK_PATH)
    print(f"saved pack: {PACK_PATH.name}")

    result = RegressionPackRunner().run_pack(pack)
    print(result.summary)

    report_path = Path(__file__).parent / "entropy-loop.report.json"
    write_json_report(result, report_path)
    print(f"wrote report: {report_path.name}")
    print(f"CI exit code would be: {0 if result.success else 1}")


if __name__ == "__main__":
    main()
