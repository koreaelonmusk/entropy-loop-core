"""Tests for CI evidence bundles, step summary, and the GitHub Action."""

from __future__ import annotations

import json
from pathlib import Path

from entropy_loop_core import (
    CIEvidenceBundle,
    CIEvidenceWriter,
    RegressionTriageEngine,
    TriagePolicy,
    append_github_step_summary,
    export_github_step_summary,
)

ACTION_YML = Path(__file__).resolve().parents[1] / "action.yml"


def _report(name: str, cases: dict[str, tuple[str, str | None]]) -> dict:
    passed = sum(1 for s, _ in cases.values() if s == "passed")
    failed = sum(1 for s, _ in cases.values() if s == "failed")
    return {
        "pack": name,
        "cases": len(cases),
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "success": failed == 0,
        "summary": f"{name} report",
        "case_results": [
            {"case": cid, "status": s, "message": m}
            for cid, (s, m) in sorted(cases.items())
        ],
    }


def _triage(policy: str = "new-failures"):
    base = _report("p", {"a": ("passed", None), "b": ("failed", "boom")})
    curr = _report("p", {"a": ("failed", "boom"), "b": ("passed", None)})
    return RegressionTriageEngine().compare_reports(
        base, curr, TriagePolicy(fail_on=policy)
    )


# --- CIEvidenceWriter -----------------------------------------------------


def test_writer_creates_bundle_files(tmp_path) -> None:
    bundle = CIEvidenceWriter().write_bundle(_triage(), tmp_path / "evidence")
    assert isinstance(bundle, CIEvidenceBundle)
    d = tmp_path / "evidence"
    for name in ("triage.json", "triage.md", "summary.txt", "manifest.json"):
        assert (d / name).exists()
    assert bundle.files == ["manifest.json", "summary.txt", "triage.json", "triage.md"]


def test_writer_records_counts_and_policy(tmp_path) -> None:
    bundle = CIEvidenceWriter().write_bundle(
        _triage("any-failures"), tmp_path / "e", policy="any-failures"
    )
    assert bundle.new_failure_count == 1
    assert bundle.fixed_count == 1
    assert bundle.policy == "any-failures"
    assert bundle.case_count == 2


def test_writer_extra_report_paths(tmp_path) -> None:
    jp = tmp_path / "out" / "triage.json"
    mp = tmp_path / "out" / "triage.md"
    bundle = CIEvidenceWriter().write_bundle(
        _triage(), tmp_path / "e", json_report_path=jp, markdown_report_path=mp
    )
    assert jp.exists() and mp.exists()
    assert bundle.json_report_path == str(jp)
    assert bundle.markdown_report_path == str(mp)


def test_writer_is_deterministic(tmp_path) -> None:
    CIEvidenceWriter().write_bundle(_triage(), tmp_path / "a")
    CIEvidenceWriter().write_bundle(_triage(), tmp_path / "b")
    for name in ("triage.json", "triage.md", "summary.txt", "manifest.json"):
        assert (tmp_path / "a" / name).read_text() == (
            tmp_path / "b" / name
        ).read_text()


def test_manifest_has_no_timestamp(tmp_path) -> None:
    CIEvidenceWriter().write_bundle(_triage(), tmp_path / "e")
    manifest = json.loads((tmp_path / "e" / "manifest.json").read_text())
    assert "timestamp" not in manifest and "time" not in manifest
    assert manifest["files"] == [
        "manifest.json",
        "summary.txt",
        "triage.json",
        "triage.md",
    ]


def test_summary_txt_has_no_timestamp(tmp_path) -> None:
    CIEvidenceWriter().write_bundle(_triage(), tmp_path / "e")
    text = (tmp_path / "e" / "summary.txt").read_text()
    assert "Entropy Loop CI evidence" in text
    assert "policy: new-failures" in text
    # Deterministic: no date-like tokens.
    assert "2026" not in text


def test_writer_only_writes_inside_dir(tmp_path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("keep")
    CIEvidenceWriter().write_bundle(_triage(), tmp_path / "e")
    assert outside.read_text() == "keep"  # untouched
    assert sorted(p.name for p in (tmp_path / "e").iterdir()) == [
        "manifest.json",
        "summary.txt",
        "triage.json",
        "triage.md",
    ]


# --- step summary ---------------------------------------------------------


def test_export_step_summary_contents() -> None:
    md = export_github_step_summary(_triage())
    assert "## Entropy Loop — regression triage" in md
    assert "policy: `new-failures`" in md
    assert "New failures: 1" in md
    assert "`a`" in md  # newly failing case


def test_export_step_summary_deterministic() -> None:
    assert export_github_step_summary(_triage()) == export_github_step_summary(
        _triage()
    )
    assert "2026" not in export_github_step_summary(_triage())


def test_append_step_summary_to_path(tmp_path) -> None:
    path = tmp_path / "summary.md"
    assert append_github_step_summary(_triage(), path) is True
    assert "regression triage" in path.read_text()


def test_append_step_summary_uses_env(tmp_path, monkeypatch) -> None:
    path = tmp_path / "env_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(path))
    assert append_github_step_summary(_triage()) is True
    assert path.exists()


def test_append_step_summary_returns_false_without_target(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert append_github_step_summary(_triage()) is False


def test_step_summary_compatibility_note_when_no_cases() -> None:
    # Minimal reports without case_results -> zero transitions.
    triage = RegressionTriageEngine().compare_reports(
        {"pack": "p"}, {"pack": "p"}, TriagePolicy()
    )
    md = export_github_step_summary(triage)
    assert "predate v0.7.0" in md


# --- action.yml -----------------------------------------------------------


def test_action_yml_exists() -> None:
    assert ACTION_YML.is_file()


def test_action_yml_required_inputs_present() -> None:
    text = ACTION_YML.read_text()
    assert "baseline-report:" in text
    assert "current-report:" in text
    assert "fail-on:" in text
    assert "evidence-dir:" in text
    assert "write-step-summary:" in text


def test_action_yml_invokes_write_ci_evidence() -> None:
    assert "entropy-loop write-ci-evidence" in ACTION_YML.read_text()


def test_action_yml_no_github_api_or_token() -> None:
    text = ACTION_YML.read_text().lower()
    assert "gh api" not in text
    assert "curl" not in text
    assert "github_token" not in text
    assert "api.github.com" not in text


def test_action_yml_is_composite() -> None:
    assert 'using: "composite"' in ACTION_YML.read_text()


def test_action_yml_has_package_version_input() -> None:
    assert "package-version:" in ACTION_YML.read_text()


def test_action_yml_infers_version_from_action_ref() -> None:
    text = ACTION_YML.read_text()
    # Uses the runner-provided ref (no GitHub API) to pin the install.
    assert "GITHUB_ACTION_REF" in text
    # Converts a vX.Y.Z tag to X.Y.Z and pins the install to it.
    assert "GITHUB_ACTION_REF#v" in text
    assert "grep -Eq" in text and "v[0-9]+" in text
    assert "entropy-loop-core==$ACTION_VERSION" in text


def test_action_yml_branch_ref_falls_back_to_latest() -> None:
    text = ACTION_YML.read_text()
    # The else branch (branch refs, no package-version) installs unpinned.
    assert 'PACKAGE_SPEC="entropy-loop-core"' in text


def test_action_yml_explicit_version_takes_precedence() -> None:
    text = ACTION_YML.read_text()
    assert "entropy-loop-core==$PACKAGE_VERSION" in text


def test_action_yml_has_junit_report_input() -> None:
    assert "junit-report:" in ACTION_YML.read_text()


def test_action_yml_junit_passthrough_is_conditional() -> None:
    text = ACTION_YML.read_text()
    # Only pass --junit-report when the input is non-empty.
    assert 'if [ -n "${{ inputs.junit-report }}" ]' in text
    assert "--junit-report" in text


def test_action_yml_no_artifact_upload() -> None:
    assert "upload-artifact" not in ACTION_YML.read_text()
