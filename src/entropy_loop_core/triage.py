"""Deterministic baseline-vs-current triage for regression reports.

Where :mod:`entropy_loop_core.regression_pack` decides *whether* a regression run
passed, this module explains *what changed* between two runs. Given a baseline
JSON report and a current JSON report (as written by ``run-pack --json-report``),
:class:`RegressionTriageEngine` classifies each case's movement — newly failing,
fixed, still failing, still passing, skipped, or missing — and rolls the
transitions up into a :class:`RegressionTriage`.

Everything here is deterministic and local: it reads two JSON files (or two
dicts), compares them, and emits a JSON or Markdown report. No LLM calls, no
network, no GitHub API, no telemetry, no hidden persistence, and no root-cause
analysis — only an honest diff of two reports.

The diff is driven by the ``case_results`` list in each report (added in v0.7.0).
Older reports without it still compare at the aggregate level, but produce no
per-case transitions; this limitation is reported, not hidden.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

# --- statuses and transitions ---------------------------------------------

# Stable, serialized-as-string case statuses.
CASE_STATUSES = (
    "passed",
    "failed",
    "skipped",
    "missing",
    "invalid",
    "unknown",
)

# A case present in one report but absent from the other uses this sentinel.
_MISSING = "missing"

_FAIL_ON_VALUES = ("new-failures", "any-failures", "never")


class CaseTransition(BaseModel):
    """One case's movement from baseline to current.

    Attributes:
        case_id: The case identifier (its name).
        baseline_status: The case status in the baseline report.
        current_status: The case status in the current report.
        transition: A stable label describing the movement (see module docs).
        summary: A deterministic one-line description of the transition.
        baseline_message: The baseline failure/skip message, if any.
        current_message: The current failure/skip message, if any.
    """

    case_id: str = Field(..., description="Case identifier.")
    baseline_status: str = Field(..., description="Status in the baseline report.")
    current_status: str = Field(..., description="Status in the current report.")
    transition: str = Field(..., description="Stable transition label.")
    summary: str = Field(..., description="Deterministic one-line description.")
    baseline_message: str | None = Field(
        default=None, description="Baseline failure/skip message, if any."
    )
    current_message: str | None = Field(
        default=None, description="Current failure/skip message, if any."
    )


class RegressionTriage(BaseModel):
    """The full diff between a baseline and a current regression report.

    Attributes:
        baseline_name: The baseline report's pack name, if present.
        current_name: The current report's pack name, if present.
        case_count: Number of distinct cases across both reports.
        new_failure_count: Cases that passed in baseline and fail now.
        fixed_count: Cases that failed in baseline and pass now.
        persistent_failure_count: Cases failing in both.
        persistent_pass_count: Cases passing in both.
        skipped_count: Cases skipped in the current report.
        missing_count: Cases present in baseline but absent in current.
        transitions: Per-case transitions, ordered by case id.
        success: Whether the triage passes under its policy.
        summary: A deterministic one-line summary.
    """

    baseline_name: str | None = Field(default=None, description="Baseline pack name.")
    current_name: str | None = Field(default=None, description="Current pack name.")
    case_count: int = Field(
        ..., ge=0, description="Distinct cases across both reports."
    )
    new_failure_count: int = Field(..., ge=0, description="Newly failing cases.")
    fixed_count: int = Field(..., ge=0, description="Newly fixed cases.")
    persistent_failure_count: int = Field(
        ..., ge=0, description="Cases failing in both."
    )
    persistent_pass_count: int = Field(..., ge=0, description="Cases passing in both.")
    skipped_count: int = Field(..., ge=0, description="Cases skipped in current.")
    missing_count: int = Field(..., ge=0, description="Cases missing in current.")
    transitions: list[CaseTransition] = Field(
        default_factory=list, description="Per-case transitions, ordered by case id."
    )
    success: bool = Field(..., description="Whether the triage passes its policy.")
    summary: str = Field(..., description="Deterministic one-line summary.")


class TriagePolicy(BaseModel):
    """Controls when a triage should fail CI.

    Attributes:
        fail_on: One of ``"new-failures"`` (default), ``"any-failures"``, or
            ``"never"``.

    - ``new-failures``: fail only when a case that passed in the baseline now
      fails. Persistent failures are reported but do not fail the triage.
    - ``any-failures``: fail if the current report has any failing case (new or
      persistent).
    - ``never``: always pass (given valid inputs).
    """

    fail_on: str = Field(default="new-failures", description="Failure policy.")

    @field_validator("fail_on")
    @classmethod
    def _check_fail_on(cls, value: str) -> str:
        if value not in _FAIL_ON_VALUES:
            allowed = ", ".join(_FAIL_ON_VALUES)
            raise ValueError(f"invalid fail_on {value!r} (expected one of: {allowed})")
        return value


# --- transition classification --------------------------------------------


def _classify(baseline_status: str, current_status: str) -> str:
    """Return the stable transition label for a status pair."""
    if baseline_status == _MISSING:
        return "new_case"
    if current_status == _MISSING:
        return "missing_in_current"
    if current_status == "skipped":
        return "still_skipped" if baseline_status == "skipped" else "new_skip"
    if baseline_status == "skipped":
        # Was skipped, now has a result — a change, but not a clean fix/regression.
        return "changed"
    if baseline_status == "passed" and current_status == "failed":
        return "new_failure"
    if baseline_status == "failed" and current_status == "passed":
        return "fixed"
    if baseline_status == "failed" and current_status == "failed":
        return "persistent_failure"
    if baseline_status == "passed" and current_status == "passed":
        return "persistent_pass"
    if baseline_status == current_status:
        return "unknown"
    return "changed"


_TRANSITION_SUMMARY = {
    "new_failure": "newly failing",
    "fixed": "fixed",
    "persistent_failure": "still failing",
    "persistent_pass": "still passing",
    "new_skip": "now skipped",
    "still_skipped": "still skipped",
    "missing_in_current": "missing in current report",
    "new_case": "new case",
}


def _summarize_transition(case_id: str, transition: str, base: str, curr: str) -> str:
    """Build a deterministic one-line summary for a transition."""
    label = _TRANSITION_SUMMARY.get(transition)
    if label is None:
        label = f"{base} → {curr}"
    return f"{case_id}: {label}"


# --- report parsing -------------------------------------------------------


def _extract_cases(report: dict[str, Any]) -> dict[str, tuple[str, str | None]]:
    """Map case id -> (status, message) from a report's ``case_results``.

    Reports without a ``case_results`` list (older/minimal reports) yield an
    empty mapping, so the triage degrades to aggregate-only with no per-case
    transitions rather than raising.
    """
    entries = report.get("case_results")
    if not isinstance(entries, list):
        return {}
    cases: dict[str, tuple[str, str | None]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or "case" not in entry:
            continue
        case_id = str(entry["case"])
        status = entry.get("status", "unknown")
        status = status if status in CASE_STATUSES else "unknown"
        message = entry.get("message")
        message = str(message) if message is not None else None
        cases[case_id] = (status, message)
    return cases


# --- engine ---------------------------------------------------------------


class RegressionTriageEngine:
    """Compares a baseline regression report against a current one.

    The engine takes explicit report dicts or local JSON file paths — there is no
    hidden baseline location and no auto-discovery. Comparison is deterministic
    and ordered by case id.
    """

    def compare_reports(
        self,
        baseline: dict[str, Any],
        current: dict[str, Any],
        policy: TriagePolicy | None = None,
    ) -> RegressionTriage:
        """Compare two report dicts and return a :class:`RegressionTriage`.

        Args:
            baseline: The baseline report (as a dict).
            current: The current report (as a dict).
            policy: The failure policy; defaults to ``fail-on new-failures``.

        Returns:
            A :class:`RegressionTriage` describing every case transition.
        """
        policy = policy or TriagePolicy()
        base_cases = _extract_cases(baseline)
        curr_cases = _extract_cases(current)

        transitions: list[CaseTransition] = []
        for case_id in sorted(set(base_cases) | set(curr_cases)):
            base_status, base_message = base_cases.get(case_id, (_MISSING, None))
            curr_status, curr_message = curr_cases.get(case_id, (_MISSING, None))
            transition = _classify(base_status, curr_status)
            transitions.append(
                CaseTransition(
                    case_id=case_id,
                    baseline_status=base_status,
                    current_status=curr_status,
                    transition=transition,
                    summary=_summarize_transition(
                        case_id, transition, base_status, curr_status
                    ),
                    baseline_message=base_message,
                    current_message=curr_message,
                )
            )

        def count(name: str) -> int:
            return sum(1 for t in transitions if t.transition == name)

        new_failure = count("new_failure")
        fixed = count("fixed")
        persistent_failure = count("persistent_failure")
        persistent_pass = count("persistent_pass")
        skipped = count("new_skip") + count("still_skipped")
        missing = count("missing_in_current")

        success = _passes_policy(policy, new_failure, persistent_failure)
        summary = (
            f"Triage: {new_failure} new failures, {fixed} fixed, "
            f"{persistent_failure} persistent failures, {persistent_pass} passing, "
            f"{skipped} skipped, {missing} missing."
        )
        return RegressionTriage(
            baseline_name=_report_name(baseline),
            current_name=_report_name(current),
            case_count=len(transitions),
            new_failure_count=new_failure,
            fixed_count=fixed,
            persistent_failure_count=persistent_failure,
            persistent_pass_count=persistent_pass,
            skipped_count=skipped,
            missing_count=missing,
            transitions=transitions,
            success=success,
            summary=summary,
        )

    def compare_report_files(
        self,
        baseline_path: str | Path,
        current_path: str | Path,
        policy: TriagePolicy | None = None,
    ) -> RegressionTriage:
        """Load two JSON reports from local paths and compare them.

        Args:
            baseline_path: Path to the baseline report JSON.
            current_path: Path to the current report JSON.
            policy: The failure policy; defaults to ``fail-on new-failures``.

        Returns:
            A :class:`RegressionTriage`.

        Raises:
            FileNotFoundError: If either path does not exist.
            ValueError: If either file is not a JSON object.
        """
        baseline = _load_report(baseline_path)
        current = _load_report(current_path)
        return self.compare_reports(baseline, current, policy)


def _passes_policy(
    policy: TriagePolicy, new_failure: int, persistent_failure: int
) -> bool:
    """Apply the failure policy to the counts."""
    if policy.fail_on == "never":
        return True
    if policy.fail_on == "any-failures":
        return (new_failure + persistent_failure) == 0
    # "new-failures"
    return new_failure == 0


def _report_name(report: dict[str, Any]) -> str | None:
    """Return the report's pack name, if present."""
    name = report.get("pack")
    return str(name) if name is not None else None


def _load_report(path: str | Path) -> dict[str, Any]:
    """Read a JSON report object from a local path."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"report not found: {path}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"report is not a JSON object: {path}")
    return data


# --- serialization --------------------------------------------------------


def export_regression_triage(triage: RegressionTriage) -> dict[str, Any]:
    """Render a triage as a plain, JSON-compatible dictionary."""
    return triage.model_dump()


def write_regression_triage_json(triage: RegressionTriage, path: str | Path) -> None:
    """Write a triage JSON report to ``path`` (creating parent directories)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(export_regression_triage(triage), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _section(title: str, transitions: list[CaseTransition]) -> list[str]:
    """Render one Markdown section for a group of transitions (or a dash)."""
    lines = [f"### {title}", ""]
    if not transitions:
        lines.append("_none_")
    else:
        for transition in transitions:
            message = transition.current_message or transition.baseline_message
            suffix = f" — {message}" if message else ""
            lines.append(f"- `{transition.case_id}`{suffix}")
    lines.append("")
    return lines


def export_regression_triage_markdown(triage: RegressionTriage) -> str:
    """Render a triage as a deterministic, human-readable Markdown report."""

    def group(name: str) -> list[CaseTransition]:
        return [t for t in triage.transitions if t.transition == name]

    lines = ["# Regression triage", ""]
    lines.append(triage.summary)
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- New failures: {triage.new_failure_count}")
    lines.append(f"- Fixed: {triage.fixed_count}")
    lines.append(f"- Persistent failures: {triage.persistent_failure_count}")
    lines.append(f"- Persistent passes: {triage.persistent_pass_count}")
    lines.append(f"- Skipped: {triage.skipped_count}")
    lines.append(f"- Missing in current: {triage.missing_count}")
    lines.append(f"- Result: {'pass' if triage.success else 'fail'}")
    lines.append("")
    lines.append("## Cases")
    lines.append("")
    lines.extend(_section("Newly failing", group("new_failure")))
    lines.extend(_section("Fixed", group("fixed")))
    lines.extend(_section("Persistent failures", group("persistent_failure")))
    lines.extend(
        _section(
            "Skipped or missing",
            group("new_skip") + group("still_skipped") + group("missing_in_current"),
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def write_regression_triage_markdown(
    triage: RegressionTriage, path: str | Path
) -> None:
    """Write a triage Markdown report to ``path`` (creating parent directories)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export_regression_triage_markdown(triage), encoding="utf-8")
