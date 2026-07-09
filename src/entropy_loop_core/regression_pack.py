"""Portable regression packs and a CI gate.

A :class:`RegressionPack` bundles regression cases with everything needed to
replay them deterministically: a :class:`VerificationPolicy` and a reference
output per case. That makes a pack a **self-contained, inspectable file** you can
commit to a repo and run in CI — no live agent, no network, no hidden state.

`RegressionPackRunner` replays a pack through the existing
:class:`~entropy_loop_core.replay.RegressionRunner` and returns a
:class:`RegressionPackResult`. The CLI (`entropy-loop run-pack`) uses stable exit
codes so a reappearing agent regression fails the build.

Everything here is deterministic and pure Python — no LLM calls, no network, no
database, no telemetry, no hidden persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape, quoteattr

from pydantic import BaseModel, Field, field_validator

from .replay import RegressionRunner
from .types import (
    AgentOutput,
    RegressionCase,
    RegressionReport,
    RegressionSuite,
    RetryContext,
    Task,
)
from .verification import VerificationPolicy, Verifier

_SCHEMA_VERSION = "1"


class RegressionPack(BaseModel):
    """A portable, runnable collection of regression cases.

    Attributes:
        name: A non-empty name for the pack.
        schema_version: The pack schema version (currently ``"1"``).
        version: A caller-managed content version.
        created_by: Who produced the pack.
        policy: The verification policy used to check each case's output.
        cases: The regression cases in the pack.
        outputs: Reference output content per case name, used to replay the pack.
        metadata: Optional free-form context.
    """

    name: str = Field(..., min_length=1, description="Non-empty pack name.")
    schema_version: str = Field(default=_SCHEMA_VERSION, description="Schema version.")
    version: str = Field(default="1", description="Caller-managed content version.")
    created_by: str = Field(
        default="entropy-loop-core", description="Who produced the pack."
    )
    policy: VerificationPolicy = Field(
        default_factory=VerificationPolicy, description="Verification policy."
    )
    cases: list[RegressionCase] = Field(
        default_factory=list, description="Regression cases in the pack."
    )
    outputs: dict[str, str] = Field(
        default_factory=dict, description="Reference output per case name."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional free-form context."
    )

    @field_validator("schema_version")
    @classmethod
    def _check_schema(cls, value: str) -> str:
        if value != _SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {value!r} (expected {_SCHEMA_VERSION!r})"
            )
        return value


class RegressionPackResult(BaseModel):
    """The outcome of running a regression pack.

    Attributes:
        pack_name: The name of the pack that was run.
        case_count: How many cases the pack had.
        passed_count: How many cases passed.
        failed_count: How many cases failed.
        skipped_count: Cases skipped because they had no reference output.
        success: True when no case failed.
        report: The underlying regression report, if available.
        summary: A deterministic one-line summary.
    """

    pack_name: str = Field(..., description="Name of the pack run.")
    case_count: int = Field(..., ge=0, description="Cases in the pack.")
    passed_count: int = Field(..., ge=0, description="Cases that passed.")
    failed_count: int = Field(..., ge=0, description="Cases that failed.")
    skipped_count: int = Field(default=0, ge=0, description="Cases skipped.")
    success: bool = Field(..., description="True when no case failed.")
    report: RegressionReport | None = Field(
        default=None, description="Underlying regression report."
    )
    summary: str = Field(..., description="Deterministic one-line summary.")


class RegressionPackRunner:
    """Runs a :class:`RegressionPack` deterministically.

    Cases with a reference output in ``pack.outputs`` are replayed through the
    pack's policy; cases without one are skipped. Reuses the existing
    :class:`RegressionRunner` rather than duplicating replay logic.
    """

    def run_pack(
        self, pack: RegressionPack, runner: RegressionRunner | None = None
    ) -> RegressionPackResult:
        """Run every runnable case in ``pack`` and summarize the outcome.

        Args:
            pack: The regression pack to run.
            runner: An optional :class:`RegressionRunner` to reuse.

        Returns:
            A :class:`RegressionPackResult`.
        """
        runner = runner or RegressionRunner()
        verifier = Verifier.from_policy(pack.policy)
        runnable = [case for case in pack.cases if case.name in pack.outputs]
        skipped = len(pack.cases) - len(runnable)
        outputs = pack.outputs

        def agent(task: Task, context: RetryContext) -> AgentOutput:
            return AgentOutput(content=outputs.get(task.id, ""))

        suite = RegressionSuite(name=pack.name, cases=runnable)
        report = runner.run_suite(suite, agent, verifier)
        passed, failed = report.passed, report.failed
        success = failed == 0
        summary = (
            f"Regression pack `{pack.name}` completed: "
            f"{passed} passed, {failed} failed, {skipped} skipped."
        )
        return RegressionPackResult(
            pack_name=pack.name,
            case_count=len(pack.cases),
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            success=success,
            report=report,
            summary=summary,
        )

    def run_pack_file(
        self, path: str | Path, runner: RegressionRunner | None = None
    ) -> RegressionPackResult:
        """Load a pack from ``path`` and run it."""
        return self.run_pack(load_regression_pack(path), runner)


# --- serialization --------------------------------------------------------


def export_regression_pack(pack: RegressionPack) -> dict[str, Any]:
    """Render a regression pack as a plain, JSON-compatible dictionary."""
    return pack.model_dump()


def import_regression_pack(data: dict[str, Any]) -> RegressionPack:
    """Build a regression pack from a plain dictionary."""
    return RegressionPack.model_validate(data)


def save_regression_pack(pack: RegressionPack, path: str | Path) -> None:
    """Write a regression pack to a local JSON file (stable key ordering)."""
    Path(path).write_text(
        json.dumps(export_regression_pack(pack), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_regression_pack(path: str | Path) -> RegressionPack:
    """Read a regression pack from a local JSON file."""
    return import_regression_pack(json.loads(Path(path).read_text(encoding="utf-8")))


def export_regression_pack_result(result: RegressionPackResult) -> dict[str, Any]:
    """Render a pack result as a plain, JSON-compatible dictionary."""
    return result.model_dump()


# --- report output --------------------------------------------------------


def export_json_report(result: RegressionPackResult) -> dict[str, Any]:
    """Render a compact, machine-readable JSON report of a pack run."""
    return {
        "pack": result.pack_name,
        "cases": result.case_count,
        "passed": result.passed_count,
        "failed": result.failed_count,
        "skipped": result.skipped_count,
        "success": result.success,
        "summary": result.summary,
    }


def write_json_report(result: RegressionPackResult, path: str | Path) -> None:
    """Write a JSON report to ``path`` (creating parent directories)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(export_json_report(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def export_junit_report(result: RegressionPackResult) -> str:
    """Render a minimal, valid JUnit XML report of a pack run."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append(
        f"<testsuite name={quoteattr(result.pack_name)} "
        f'tests="{result.case_count}" failures="{result.failed_count}" '
        f'skipped="{result.skipped_count}">'
    )
    if result.report is not None:
        for case_result in result.report.results:
            name = quoteattr(case_result.case.name)
            classname = quoteattr(result.pack_name)
            if case_result.passed:
                lines.append(f"  <testcase classname={classname} name={name}/>")
            else:
                reason = (
                    case_result.verification_result.reason
                    if case_result.verification_result
                    else (case_result.error or "failed")
                )
                lines.append(f"  <testcase classname={classname} name={name}>")
                lines.append(f"    <failure>{escape(reason)}</failure>")
                lines.append("  </testcase>")
    lines.append("</testsuite>")
    return "\n".join(lines) + "\n"


def write_junit_report(result: RegressionPackResult, path: str | Path) -> None:
    """Write a JUnit XML report to ``path`` (creating parent directories)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export_junit_report(result), encoding="utf-8")
