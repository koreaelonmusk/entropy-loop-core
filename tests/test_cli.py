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
