"""Deterministic CI evidence bundles and a GitHub Actions step summary.

Where :mod:`entropy_loop_core.triage` explains what changed between two runs,
this module packages that explanation into a reviewable, local **evidence
bundle** and, when running inside GitHub Actions, appends a compact summary to
the step summary. It is the local half of the first-party GitHub Action.

Everything here is deterministic and local: it writes files into a directory you
name and reads exactly one environment variable (``GITHUB_STEP_SUMMARY``) when
you ask it to append a step summary. No LLM calls, no network, no GitHub API, no
tokens, no telemetry, no hidden persistence, and no root-cause analysis.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

from .triage import (
    RegressionTriage,
    write_regression_triage_json,
    write_regression_triage_markdown,
)

# The fixed, sorted set of files a bundle always writes into the evidence dir.
_BUNDLE_FILES = ("manifest.json", "summary.txt", "triage.json", "triage.md")


class CIEvidenceBundle(BaseModel):
    """A deterministic description of a written CI evidence directory.

    Attributes:
        summary: The triage's one-line summary.
        success: Whether the triage passed its policy.
        policy: The fail-on policy applied.
        json_report_path: Extra JSON report path written, if any.
        markdown_report_path: Extra Markdown report path written, if any.
        evidence_dir: The evidence directory, as a string.
        files: The bundle file names inside the evidence dir, sorted.
        new_failure_count: Newly failing cases.
        fixed_count: Newly fixed cases.
        persistent_failure_count: Cases failing in both runs.
        case_count: Distinct cases compared.
    """

    summary: str = Field(..., description="Triage one-line summary.")
    success: bool = Field(..., description="Whether the triage passed its policy.")
    policy: str = Field(..., description="The fail-on policy applied.")
    json_report_path: str | None = Field(
        default=None, description="Extra JSON report path written, if any."
    )
    markdown_report_path: str | None = Field(
        default=None, description="Extra Markdown report path written, if any."
    )
    evidence_dir: str | None = Field(
        default=None, description="The evidence directory, as a string."
    )
    files: list[str] = Field(
        default_factory=list, description="Bundle file names inside the dir, sorted."
    )
    new_failure_count: int = Field(..., ge=0, description="Newly failing cases.")
    fixed_count: int = Field(..., ge=0, description="Newly fixed cases.")
    persistent_failure_count: int = Field(
        ..., ge=0, description="Cases failing in both."
    )
    case_count: int = Field(..., ge=0, description="Distinct cases compared.")


def _policy_of(triage: RegressionTriage, override: str | None) -> str:
    """Resolve the policy name from an override, the triage, or the default."""
    return override or triage.policy or "new-failures"


def _summary_text(triage: RegressionTriage, policy: str) -> str:
    """Render a deterministic plain-text summary (no timestamps)."""
    return (
        "\n".join(
            [
                "Entropy Loop CI evidence",
                triage.summary,
                f"policy: {policy}",
                f"result: {'pass' if triage.success else 'fail'}",
                f"new failures: {triage.new_failure_count}",
                f"fixed: {triage.fixed_count}",
                f"persistent failures: {triage.persistent_failure_count}",
                f"cases: {triage.case_count}",
            ]
        )
        + "\n"
    )


class CIEvidenceWriter:
    """Writes a deterministic local evidence directory from a triage.

    The bundle always contains ``triage.json``, ``triage.md``, ``summary.txt``,
    and ``manifest.json``. Only these fixed file names are written, all inside
    the evidence directory you name — nothing is written or deleted outside it.
    """

    def write_bundle(
        self,
        triage: RegressionTriage,
        evidence_dir: str | Path,
        *,
        policy: str | None = None,
        json_report_path: str | Path | None = None,
        markdown_report_path: str | Path | None = None,
    ) -> CIEvidenceBundle:
        """Write an evidence bundle and return its description.

        Args:
            triage: The triage to package.
            evidence_dir: The directory to write the bundle into (created).
            policy: The fail-on policy name; falls back to ``triage.policy`` then
                ``"new-failures"``.
            json_report_path: Optional extra path to also write the JSON report.
            markdown_report_path: Optional extra path to also write the Markdown
                report.

        Returns:
            A :class:`CIEvidenceBundle` describing what was written.
        """
        policy_name = _policy_of(triage, policy)
        directory = Path(evidence_dir)
        directory.mkdir(parents=True, exist_ok=True)

        write_regression_triage_json(triage, directory / "triage.json")
        write_regression_triage_markdown(triage, directory / "triage.md")
        (directory / "summary.txt").write_text(
            _summary_text(triage, policy_name), encoding="utf-8"
        )

        manifest = {
            "case_count": triage.case_count,
            "files": list(_BUNDLE_FILES),
            "fixed_count": triage.fixed_count,
            "new_failure_count": triage.new_failure_count,
            "persistent_failure_count": triage.persistent_failure_count,
            "policy": policy_name,
            "success": triage.success,
            "summary": triage.summary,
        }
        (directory / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        if json_report_path is not None:
            write_regression_triage_json(triage, json_report_path)
        if markdown_report_path is not None:
            write_regression_triage_markdown(triage, markdown_report_path)

        return CIEvidenceBundle(
            summary=triage.summary,
            success=triage.success,
            policy=policy_name,
            json_report_path=str(json_report_path) if json_report_path else None,
            markdown_report_path=(
                str(markdown_report_path) if markdown_report_path else None
            ),
            evidence_dir=str(evidence_dir),
            files=list(_BUNDLE_FILES),
            new_failure_count=triage.new_failure_count,
            fixed_count=triage.fixed_count,
            persistent_failure_count=triage.persistent_failure_count,
            case_count=triage.case_count,
        )


# --- GitHub Actions step summary ------------------------------------------


def _summary_cases(triage: RegressionTriage, transition: str) -> list[str]:
    """Case ids for a transition, ordered as in the triage."""
    return [t.case_id for t in triage.transitions if t.transition == transition]


def export_github_step_summary(triage: RegressionTriage) -> str:
    """Render a compact, deterministic GitHub Actions step summary (Markdown)."""
    policy = triage.policy or "new-failures"
    result = "pass ✅" if triage.success else "fail ❌"
    lines = [
        "## Entropy Loop — regression triage",
        "",
        f"**Result:** {result} (policy: `{policy}`)",
        "",
        f"- New failures: {triage.new_failure_count}",
        f"- Fixed: {triage.fixed_count}",
        f"- Persistent failures: {triage.persistent_failure_count}",
        f"- Cases compared: {triage.case_count}",
        "",
    ]

    def block(title: str, transition: str) -> None:
        cases = _summary_cases(triage, transition)
        if cases:
            lines.append(f"**{title}:** " + ", ".join(f"`{c}`" for c in cases))

    block("Newly failing", "new_failure")
    block("Fixed", "fixed")
    block("Persistent failures", "persistent_failure")

    if triage.case_count == 0:
        lines.append("")
        lines.append(
            "_No per-case data: the baseline report may predate v0.7.0 "
            "`case_results`. Regenerate baselines with v0.7.0 or later._"
        )

    return "\n".join(lines).rstrip() + "\n"


def append_github_step_summary(
    triage: RegressionTriage, path: str | Path | None = None
) -> bool:
    """Append a step summary to ``path`` or ``$GITHUB_STEP_SUMMARY``.

    Args:
        triage: The triage to summarize.
        path: An explicit file to append to. When ``None``, the single
            environment variable ``GITHUB_STEP_SUMMARY`` is read.

    Returns:
        ``True`` if a summary was written; ``False`` when no path is available
        (outside GitHub Actions, with no explicit path) — never raises for that.
    """
    target = path if path is not None else os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return False
    summary = export_github_step_summary(triage)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(summary)
    return True


# --- convenience ----------------------------------------------------------


def export_ci_evidence_bundle(bundle: CIEvidenceBundle) -> dict:
    """Render an evidence bundle as a plain, JSON-compatible dictionary."""
    return bundle.model_dump()
