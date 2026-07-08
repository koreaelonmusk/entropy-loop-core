"""Smoke test for the CLI demo."""

from __future__ import annotations

from typer.testing import CliRunner

from entropy_loop_core.cli import app

runner = CliRunner()


def test_demo_runs_and_succeeds() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "Entropy Loop Demo" in result.stdout
    assert "Attempt 1 failed" in result.stdout
    assert "Loop completed successfully" in result.stdout
