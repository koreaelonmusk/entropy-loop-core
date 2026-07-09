"""Compare a baseline regression report with a current one and explain what
changed.

This mirrors what ``entropy-loop compare-reports`` does: it builds a baseline
report and a current report (here from two small packs), diffs them, prints a
deterministic summary, and writes a Markdown triage report. Everything is local
and deterministic — no network, no LLM calls.

Run it:

    python3 examples/regression_triage_demo.py
"""

from __future__ import annotations

from pathlib import Path

from entropy_loop_core import (
    RegressionCase,
    RegressionPack,
    RegressionPackRunner,
    RegressionTriageEngine,
    VerificationPolicy,
    export_json_report,
    export_regression_triage_markdown,
)


def _case(name: str) -> RegressionCase:
    return RegressionCase(
        name=name,
        instruction=f"return {name} as JSON",
        expected_rule="valid_json_when_expected",
        failure_reason="expected valid JSON",
        category="invalid_json",
    )


def _report(name: str, outputs: dict[str, str]) -> dict:
    """Run a pack and return its enriched JSON report (with per-case results)."""
    pack = RegressionPack(
        name=name,
        policy=VerificationPolicy(require_non_empty=True, expect_json=True),
        cases=[_case("json-1"), _case("json-2"), _case("json-3")],
        outputs=outputs,
    )
    return export_json_report(RegressionPackRunner().run_pack(pack))


def main() -> None:
    # Baseline: json-2 already failing.
    baseline = _report(
        "triage-demo",
        {"json-1": "{}", "json-2": "not json", "json-3": "{}"},
    )
    # Current: json-1 newly broke, json-2 got fixed.
    current = _report(
        "triage-demo",
        {"json-1": "not json", "json-2": "{}", "json-3": "{}"},
    )

    triage = RegressionTriageEngine().compare_reports(baseline, current)

    print(triage.summary)
    for transition in triage.transitions:
        print(f"  - {transition.summary}")

    out = Path("/tmp/triage.md")
    out.write_text(export_regression_triage_markdown(triage), encoding="utf-8")
    print(f"markdown report: {out}")


if __name__ == "__main__":
    main()
