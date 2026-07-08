"""Smoke tests for the CLI."""

from __future__ import annotations

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
