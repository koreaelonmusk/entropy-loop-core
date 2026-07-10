"""Smoke tests for the CLI."""

from __future__ import annotations

import sys

from typer.testing import CliRunner

from entropy_loop_core.cli import app

runner = CliRunner()


def test_demo_runs_and_reports_category_and_summary() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "Entropy Loop Demo" in result.stdout
    assert "Failure category: missing_required_term" in result.stdout
    assert "Failure fingerprint:" in result.stdout
    assert "Evaluation summary:" in result.stdout
    assert "Regression case generated:" in result.stdout


def test_doctor_passes() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "All checks passed." in result.stdout


def test_replay_demo_runs_and_passes() -> None:
    result = runner.invoke(app, ["replay-demo"])
    assert result.exit_code == 0
    assert "Entropy Loop Replay Demo" in result.stdout
    assert "Regression suite created" in result.stdout
    assert "Result: passed" in result.stdout
    assert "success_rate=100.0%" in result.stdout


def test_memory_demo_runs_and_compacts() -> None:
    result = runner.invoke(app, ["memory-demo"])
    assert result.exit_code == 0
    assert "Entropy Loop Memory Demo" in result.stdout
    assert "Lessons generated: 5" in result.stdout
    assert "Input lessons: 5" in result.stdout
    assert "Output lessons: 3" in result.stdout
    assert "Dropped: 2" in result.stdout


def test_pack_demo_runs() -> None:
    result = runner.invoke(app, ["pack-demo"])
    assert result.exit_code == 0
    assert "Entropy Loop Regression Pack Demo" in result.stdout
    assert "Pack created: json-agent-guard" in result.stdout
    assert "Passed: 3" in result.stdout


def _write_pack(path, outputs) -> None:
    from entropy_loop_core import (
        RegressionCase,
        RegressionPack,
        VerificationPolicy,
        save_regression_pack,
    )

    pack = RegressionPack(
        name="p",
        policy=VerificationPolicy(require_non_empty=True, expect_json=True),
        cases=[
            RegressionCase(
                name="a",
                instruction="return JSON",
                expected_rule="valid_json_when_expected",
                failure_reason="expected valid JSON",
                category="invalid_json",
            )
        ],
        outputs=outputs,
    )
    save_regression_pack(pack, path)


def test_run_pack_exit_0_when_passing(tmp_path) -> None:
    path = tmp_path / "pack.json"
    _write_pack(path, {"a": "{}"})
    result = runner.invoke(app, ["run-pack", str(path)])
    assert result.exit_code == 0
    assert "0 failed" in result.stdout


def test_run_pack_exit_1_when_failing(tmp_path) -> None:
    path = tmp_path / "pack.json"
    _write_pack(path, {"a": "not json"})
    result = runner.invoke(app, ["run-pack", str(path)])
    assert result.exit_code == 1
    assert "1 failed" in result.stdout


def test_run_pack_exit_2_when_missing() -> None:
    result = runner.invoke(app, ["run-pack", "does-not-exist.json"])
    assert result.exit_code == 2


def test_run_pack_exit_2_when_malformed(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{ not json")
    result = runner.invoke(app, ["run-pack", str(path)])
    assert result.exit_code == 2


def test_run_pack_writes_reports(tmp_path) -> None:
    path = tmp_path / "pack.json"
    _write_pack(path, {"a": "{}"})
    jp = tmp_path / "reports" / "r.json"
    xp = tmp_path / "reports" / "r.xml"
    result = runner.invoke(
        app,
        ["run-pack", str(path), "--json-report", str(jp), "--junit-report", str(xp)],
    )
    assert result.exit_code == 0
    assert jp.exists() and xp.exists()


_GOOD = "import sys, json; sys.stdin.read(); print(json.dumps({'v': 1}))"
_BAD = "import sys; sys.stdin.read(); sys.exit(4)"


def test_agent_demo_runs() -> None:
    result = runner.invoke(app, ["agent-demo"])
    assert result.exit_code == 0
    assert "Entropy Loop Agent Demo" in result.stdout
    assert "Refreshed: 3" in result.stdout
    assert "Passed: 3" in result.stdout


def test_refresh_pack_exit_0_and_run(tmp_path) -> None:
    src = tmp_path / "in.pack.json"
    dst = tmp_path / "out.pack.json"
    _write_pack(src, {"a": "old"})
    result = runner.invoke(
        app, ["refresh-pack", str(src), str(dst), "--", sys.executable, "-c", _GOOD]
    )
    assert result.exit_code == 0
    assert dst.exists()
    # refreshed pack passes run-pack
    run = runner.invoke(app, ["run-pack", str(dst)])
    assert run.exit_code == 0


def test_refresh_pack_exit_1_when_agent_fails(tmp_path) -> None:
    src = tmp_path / "in.pack.json"
    dst = tmp_path / "out.pack.json"
    _write_pack(src, {"a": "old"})
    result = runner.invoke(
        app, ["refresh-pack", str(src), str(dst), "--", sys.executable, "-c", _BAD]
    )
    assert result.exit_code == 1


def test_refresh_pack_exit_2_missing_input(tmp_path) -> None:
    dst = tmp_path / "out.pack.json"
    result = runner.invoke(
        app,
        ["refresh-pack", "missing.json", str(dst), "--", sys.executable, "-c", _GOOD],
    )
    assert result.exit_code == 2


def test_refresh_pack_exit_2_no_command(tmp_path) -> None:
    src = tmp_path / "in.pack.json"
    dst = tmp_path / "out.pack.json"
    _write_pack(src, {"a": "old"})
    result = runner.invoke(app, ["refresh-pack", str(src), str(dst)])
    assert result.exit_code == 2


def _write_report(path, cases) -> None:
    """Write a minimal JSON report with a case_results list for triage tests."""
    import json

    passed = sum(1 for s, _ in cases.values() if s == "passed")
    failed = sum(1 for s, _ in cases.values() if s == "failed")
    path.write_text(
        json.dumps(
            {
                "pack": "p",
                "cases": len(cases),
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "success": failed == 0,
                "summary": "report",
                "case_results": [
                    {"case": cid, "status": s, "message": m}
                    for cid, (s, m) in sorted(cases.items())
                ],
            }
        )
    )


def test_triage_demo_runs() -> None:
    result = runner.invoke(app, ["triage-demo"])
    assert result.exit_code == 0
    assert "Entropy Loop Triage Demo" in result.stdout
    assert "New failures: 1" in result.stdout
    assert "Fixed: 1" in result.stdout


def test_compare_reports_exit_0_no_new_failures(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(app, ["compare-reports", str(base), str(curr)])
    assert result.exit_code == 0


def test_compare_reports_exit_1_on_new_failure(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(app, ["compare-reports", str(base), str(curr)])
    assert result.exit_code == 1


def test_compare_reports_any_failures_policy(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("failed", "boom")})
    _write_report(curr, {"a": ("failed", "boom")})  # persistent only
    # default new-failures policy passes; any-failures fails
    ok = runner.invoke(app, ["compare-reports", str(base), str(curr)])
    assert ok.exit_code == 0
    fail = runner.invoke(
        app, ["compare-reports", str(base), str(curr), "--fail-on", "any-failures"]
    )
    assert fail.exit_code == 1


def test_compare_reports_never_policy(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(
        app, ["compare-reports", str(base), str(curr), "--fail-on", "never"]
    )
    assert result.exit_code == 0


def test_compare_reports_exit_2_missing_baseline(tmp_path) -> None:
    curr = tmp_path / "current.json"
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(app, ["compare-reports", "missing.json", str(curr)])
    assert result.exit_code == 2


def test_compare_reports_exit_2_malformed_json(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    base.write_text("{ not json")
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(app, ["compare-reports", str(base), str(curr)])
    assert result.exit_code == 2


def test_compare_reports_exit_2_invalid_policy(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(
        app, ["compare-reports", str(base), str(curr), "--fail-on", "bogus"]
    )
    assert result.exit_code == 2


def test_compare_reports_writes_reports(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    jp = tmp_path / "out" / "triage.json"
    mp = tmp_path / "out" / "triage.md"
    result = runner.invoke(
        app,
        [
            "compare-reports",
            str(base),
            str(curr),
            "--json-report",
            str(jp),
            "--markdown-report",
            str(mp),
        ],
    )
    assert result.exit_code == 0
    assert jp.exists() and mp.exists()


def test_compare_reports_writes_junit(tmp_path) -> None:
    import xml.etree.ElementTree as ET

    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    xp = tmp_path / "out" / "triage.xml"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(
        app,
        ["compare-reports", str(base), str(curr), "--junit-report", str(xp)],
    )
    assert result.exit_code == 1  # new failure under default policy
    assert xp.exists()
    root = ET.parse(xp).getroot()
    assert root.tag == "testsuites"


def test_compare_reports_junit_combines_with_json_markdown(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    jp = tmp_path / "r.json"
    mp = tmp_path / "r.md"
    xp = tmp_path / "r.xml"
    result = runner.invoke(
        app,
        [
            "compare-reports",
            str(base),
            str(curr),
            "--json-report",
            str(jp),
            "--markdown-report",
            str(mp),
            "--junit-report",
            str(xp),
        ],
    )
    assert result.exit_code == 0
    assert jp.exists() and mp.exists() and xp.exists()


def test_contract_command_exits_0() -> None:
    import json

    result = runner.invoke(app, ["contract"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["project"] == "entropy-loop-core"
    assert data["contract_version"] == "1"


def test_contract_command_writes_output(tmp_path) -> None:
    import json

    out = tmp_path / "out" / "contract.json"
    result = runner.invoke(app, ["contract", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert json.loads(out.read_text())["project"] == "entropy-loop-core"


def test_compare_reports_writes_html(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    hp = tmp_path / "out" / "report.html"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(
        app, ["compare-reports", str(base), str(curr), "--html-report", str(hp)]
    )
    assert result.exit_code == 1  # new failure
    assert hp.exists()
    assert "Entropy Loop Failure Console" in hp.read_text()


def test_compare_reports_combines_all_outputs(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    jp = tmp_path / "r.json"
    mp = tmp_path / "r.md"
    xp = tmp_path / "r.xml"
    hp = tmp_path / "r.html"
    result = runner.invoke(
        app,
        [
            "compare-reports",
            str(base),
            str(curr),
            "--json-report",
            str(jp),
            "--markdown-report",
            str(mp),
            "--junit-report",
            str(xp),
            "--html-report",
            str(hp),
        ],
    )
    assert result.exit_code == 0
    assert jp.exists() and mp.exists() and xp.exists() and hp.exists()


def test_ci_demo_runs() -> None:
    result = runner.invoke(app, ["ci-demo"])
    assert result.exit_code == 0
    assert "Entropy Loop CI Demo" in result.stdout
    assert "Evidence bundle written: 4 files" in result.stdout


def test_write_ci_evidence_exit_1_and_files(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    ev = tmp_path / "evidence"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(
        app,
        ["write-ci-evidence", str(base), str(curr), "--evidence-dir", str(ev)],
    )
    assert result.exit_code == 1  # new failure under default new-failures
    for name in ("triage.json", "triage.md", "summary.txt", "manifest.json"):
        assert (ev / name).exists()


def test_write_ci_evidence_exit_0_when_passing(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(
        app,
        [
            "write-ci-evidence",
            str(base),
            str(curr),
            "--evidence-dir",
            str(tmp_path / "e"),
        ],
    )
    assert result.exit_code == 0


def test_write_ci_evidence_writes_junit_outside_bundle(tmp_path) -> None:
    import xml.etree.ElementTree as ET

    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    ev = tmp_path / "evidence"
    xp = tmp_path / "junit.xml"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(
        app,
        [
            "write-ci-evidence",
            str(base),
            str(curr),
            "--evidence-dir",
            str(ev),
            "--junit-report",
            str(xp),
        ],
    )
    assert result.exit_code == 1  # new failure
    # JUnit written, but the default bundle is still exactly 4 files.
    assert xp.exists()
    ET.parse(xp)
    assert sorted(p.name for p in ev.iterdir()) == [
        "manifest.json",
        "summary.txt",
        "triage.json",
        "triage.md",
    ]


def test_write_ci_evidence_writes_html_outside_bundle(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    ev = tmp_path / "evidence"
    hp = tmp_path / "report.html"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(
        app,
        [
            "write-ci-evidence",
            str(base),
            str(curr),
            "--evidence-dir",
            str(ev),
            "--html-report",
            str(hp),
        ],
    )
    assert result.exit_code == 1  # new failure
    assert hp.exists()
    assert "Entropy Loop Failure Console" in hp.read_text()
    # Default bundle is still exactly 4 files.
    assert sorted(p.name for p in ev.iterdir()) == [
        "manifest.json",
        "summary.txt",
        "triage.json",
        "triage.md",
    ]


def test_write_ci_evidence_never_policy(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("failed", "boom")})
    result = runner.invoke(
        app,
        [
            "write-ci-evidence",
            str(base),
            str(curr),
            "--fail-on",
            "never",
            "--evidence-dir",
            str(tmp_path / "e"),
        ],
    )
    assert result.exit_code == 0


def test_write_ci_evidence_exit_2_missing(tmp_path) -> None:
    curr = tmp_path / "current.json"
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(app, ["write-ci-evidence", "missing.json", str(curr)])
    assert result.exit_code == 2


def test_write_ci_evidence_exit_2_malformed(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    base.write_text("{ not json")
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(app, ["write-ci-evidence", str(base), str(curr)])
    assert result.exit_code == 2


def test_write_ci_evidence_exit_2_invalid_policy(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(
        app, ["write-ci-evidence", str(base), str(curr), "--fail-on", "bogus"]
    )
    assert result.exit_code == 2


def test_write_ci_evidence_appends_step_summary(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    summary = tmp_path / "step.md"
    _write_report(base, {"a": ("passed", None)})
    _write_report(curr, {"a": ("passed", None)})
    result = runner.invoke(
        app,
        [
            "write-ci-evidence",
            str(base),
            str(curr),
            "--evidence-dir",
            str(tmp_path / "e"),
            "--github-step-summary",
            str(summary),
        ],
    )
    assert result.exit_code == 0
    assert summary.exists()
    assert "regression triage" in summary.read_text()


def test_refresh_pack_writes_json_report(tmp_path) -> None:
    src = tmp_path / "in.pack.json"
    dst = tmp_path / "out.pack.json"
    rep = tmp_path / "reports" / "refresh.json"
    _write_pack(src, {"a": "old"})
    result = runner.invoke(
        app,
        [
            "refresh-pack",
            str(src),
            str(dst),
            "--json-report",
            str(rep),
            "--",
            sys.executable,
            "-c",
            _GOOD,
        ],
    )
    assert result.exit_code == 0
    assert rep.exists()
