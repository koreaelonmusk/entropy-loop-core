"""Tests for regression triage: baseline-vs-current report diffing."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest

from entropy_loop_core import (
    CaseTransition,
    RegressionTriage,
    RegressionTriageEngine,
    TriagePolicy,
    export_regression_triage,
    export_regression_triage_junit_xml,
    export_regression_triage_markdown,
    write_regression_triage_json,
    write_regression_triage_junit_xml,
    write_regression_triage_markdown,
)


def _report(name: str, cases: dict[str, tuple[str, str | None]]) -> dict:
    """Build a minimal report dict with a case_results list."""
    passed = sum(1 for status, _ in cases.values() if status == "passed")
    failed = sum(1 for status, _ in cases.values() if status == "failed")
    skipped = sum(1 for status, _ in cases.values() if status == "skipped")
    return {
        "pack": name,
        "cases": len(cases),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "success": failed == 0,
        "summary": f"{name}: {passed} passed, {failed} failed",
        "case_results": [
            {"case": cid, "status": status, "message": message}
            for cid, (status, message) in sorted(cases.items())
        ],
    }


# --- transition classification --------------------------------------------


def _transition(baseline: dict, current: dict, case_id: str) -> CaseTransition:
    triage = RegressionTriageEngine().compare_reports(baseline, current)
    return next(t for t in triage.transitions if t.case_id == case_id)


def test_new_failure() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    assert _transition(base, curr, "a").transition == "new_failure"


def test_fixed() -> None:
    base = _report("p", {"a": ("failed", "boom")})
    curr = _report("p", {"a": ("passed", None)})
    assert _transition(base, curr, "a").transition == "fixed"


def test_persistent_failure() -> None:
    base = _report("p", {"a": ("failed", "boom")})
    curr = _report("p", {"a": ("failed", "boom")})
    assert _transition(base, curr, "a").transition == "persistent_failure"


def test_persistent_pass() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("passed", None)})
    assert _transition(base, curr, "a").transition == "persistent_pass"


def test_missing_in_current() -> None:
    base = _report("p", {"a": ("passed", None), "b": ("passed", None)})
    curr = _report("p", {"a": ("passed", None)})
    assert _transition(base, curr, "b").transition == "missing_in_current"


def test_new_case() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("passed", None), "b": ("passed", None)})
    assert _transition(base, curr, "b").transition == "new_case"


def test_new_skip() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("skipped", None)})
    assert _transition(base, curr, "a").transition == "new_skip"


def test_still_skipped() -> None:
    base = _report("p", {"a": ("skipped", None)})
    curr = _report("p", {"a": ("skipped", None)})
    assert _transition(base, curr, "a").transition == "still_skipped"


def test_transition_summary_is_deterministic() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    t = _transition(base, curr, "a")
    assert t.summary == "a: newly failing"
    assert t.current_message == "boom"


# --- TriagePolicy ---------------------------------------------------------


def test_policy_default_is_new_failures() -> None:
    assert TriagePolicy().fail_on == "new-failures"


def test_policy_accepts_valid() -> None:
    for value in ("new-failures", "any-failures", "never"):
        assert TriagePolicy(fail_on=value).fail_on == value


def test_policy_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        TriagePolicy(fail_on="sometimes")


# --- engine: counts, ordering, policy -------------------------------------


def test_counts_and_stable_ordering() -> None:
    base = _report(
        "p",
        {
            "c": ("passed", None),
            "a": ("passed", None),
            "b": ("failed", "boom"),
            "d": ("failed", "boom"),
        },
    )
    curr = _report(
        "p",
        {
            "c": ("failed", "new"),  # new_failure
            "a": ("passed", None),  # persistent_pass
            "b": ("passed", None),  # fixed
            "d": ("failed", "boom"),  # persistent_failure
        },
    )
    triage = RegressionTriageEngine().compare_reports(base, curr)
    assert triage.new_failure_count == 1
    assert triage.fixed_count == 1
    assert triage.persistent_failure_count == 1
    assert triage.persistent_pass_count == 1
    assert triage.case_count == 4
    # stable ordering by case id
    assert [t.case_id for t in triage.transitions] == ["a", "b", "c", "d"]
    assert isinstance(triage, RegressionTriage)


def test_policy_new_failures() -> None:
    base = _report("p", {"a": ("failed", "boom")})
    curr = _report("p", {"a": ("failed", "boom")})  # persistent only
    triage = RegressionTriageEngine().compare_reports(
        base, curr, TriagePolicy(fail_on="new-failures")
    )
    assert triage.success is True  # persistent failure does not fail this policy


def test_policy_any_failures() -> None:
    base = _report("p", {"a": ("failed", "boom")})
    curr = _report("p", {"a": ("failed", "boom")})
    triage = RegressionTriageEngine().compare_reports(
        base, curr, TriagePolicy(fail_on="any-failures")
    )
    assert triage.success is False  # any failure fails this policy


def test_policy_never() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    triage = RegressionTriageEngine().compare_reports(
        base, curr, TriagePolicy(fail_on="never")
    )
    assert triage.success is True


def test_new_failure_fails_default_policy() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    triage = RegressionTriageEngine().compare_reports(base, curr)
    assert triage.success is False


# --- files, malformed, backward-compat ------------------------------------


def test_compare_report_files(tmp_path) -> None:
    base_path = tmp_path / "baseline.json"
    curr_path = tmp_path / "current.json"
    base_path.write_text(json.dumps(_report("p", {"a": ("passed", None)})))
    curr_path.write_text(json.dumps(_report("p", {"a": ("failed", "boom")})))
    triage = RegressionTriageEngine().compare_report_files(base_path, curr_path)
    assert triage.new_failure_count == 1


def test_missing_file_raises(tmp_path) -> None:
    curr = tmp_path / "current.json"
    curr.write_text(json.dumps(_report("p", {"a": ("passed", None)})))
    with pytest.raises(FileNotFoundError):
        RegressionTriageEngine().compare_report_files("nope.json", curr)


def test_malformed_json_raises(tmp_path) -> None:
    base = tmp_path / "baseline.json"
    curr = tmp_path / "current.json"
    base.write_text("{ not json")
    curr.write_text(json.dumps(_report("p", {"a": ("passed", None)})))
    with pytest.raises(json.JSONDecodeError):
        RegressionTriageEngine().compare_report_files(base, curr)


def test_backward_compatible_minimal_report() -> None:
    # Older reports without case_results: aggregate-only, no per-case transitions.
    base = {"pack": "p", "cases": 1, "passed": 1, "failed": 0}
    curr = {"pack": "p", "cases": 1, "passed": 0, "failed": 1}
    triage = RegressionTriageEngine().compare_reports(base, curr)
    assert triage.transitions == []
    assert triage.new_failure_count == 0
    assert triage.success is True  # nothing to compare per-case


# --- serialization --------------------------------------------------------


def test_export_json_contains_counts_and_transitions() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    triage = RegressionTriageEngine().compare_reports(base, curr)
    data = export_regression_triage(triage)
    assert data["new_failure_count"] == 1
    assert data["transitions"][0]["case_id"] == "a"


def test_write_json_report(tmp_path) -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    triage = RegressionTriageEngine().compare_reports(base, curr)
    path = tmp_path / "reports" / "triage.json"
    write_regression_triage_json(triage, path)
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["new_failure_count"] == 1


def test_export_markdown_has_sections() -> None:
    base = _report("p", {"a": ("passed", None), "b": ("failed", "boom")})
    curr = _report("p", {"a": ("failed", "boom"), "b": ("passed", None)})
    md = export_regression_triage_markdown(triage_from(base, curr))
    assert "# Regression triage" in md
    assert "### Newly failing" in md
    assert "### Fixed" in md
    assert "`a`" in md


def test_markdown_is_deterministic() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    a = export_regression_triage_markdown(triage_from(base, curr))
    b = export_regression_triage_markdown(triage_from(base, curr))
    assert a == b


def test_write_markdown_report(tmp_path) -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "boom")})
    path = tmp_path / "reports" / "triage.md"
    write_regression_triage_markdown(triage_from(base, curr), path)
    assert path.exists()
    assert "# Regression triage" in path.read_text()


def triage_from(base: dict, curr: dict) -> RegressionTriage:
    return RegressionTriageEngine().compare_reports(base, curr)


# --- JUnit XML ------------------------------------------------------------


def _mixed_triage() -> RegressionTriage:
    base = _report(
        "p",
        {"a": ("passed", None), "b": ("failed", "boom"), "c": ("passed", None)},
    )
    curr = _report(
        "p",
        {"a": ("failed", "now broke"), "b": ("failed", "boom"), "c": ("passed", None)},
    )
    return RegressionTriageEngine().compare_reports(base, curr, TriagePolicy())


def test_junit_is_valid_xml() -> None:
    xml = export_regression_triage_junit_xml(_mixed_triage())
    root = ET.fromstring(xml)
    assert root.tag == "testsuites"
    suite = root.find("testsuite")
    assert suite is not None
    assert suite.get("name") == "entropy-loop"


def test_junit_counts_match_elements() -> None:
    root = ET.fromstring(export_regression_triage_junit_xml(_mixed_triage()))
    suite = root.find("testsuite")
    cases = suite.findall("testcase")
    failures = [c for c in cases if c.find("failure") is not None]
    assert suite.get("tests") == "3"
    assert suite.get("failures") == "2"
    assert suite.get("errors") == "0"
    assert len(cases) == 3
    assert len(failures) == 2


def test_junit_new_failure_type() -> None:
    root = ET.fromstring(export_regression_triage_junit_xml(_mixed_triage()))
    a = next(c for c in root.iter("testcase") if c.get("name") == "a")
    assert a.find("failure").get("type") == "new-failure"
    b = next(c for c in root.iter("testcase") if c.get("name") == "b")
    assert b.find("failure").get("type") == "persistent-failure"


def test_junit_resolved_case_passes() -> None:
    # 'c' passed in both -> passing testcase with no failure child.
    root = ET.fromstring(export_regression_triage_junit_xml(_mixed_triage()))
    c = next(tc for tc in root.iter("testcase") if tc.get("name") == "c")
    assert c.find("failure") is None


def test_junit_is_deterministic() -> None:
    a = export_regression_triage_junit_xml(_mixed_triage())
    b = export_regression_triage_junit_xml(_mixed_triage())
    assert a == b


def test_junit_escapes_special_characters() -> None:
    base = _report("p", {"x&y": ("passed", None)})
    curr = _report("p", {"x&y": ("failed", 'a < b & c > d "q"')})
    triage = RegressionTriageEngine().compare_reports(base, curr)
    xml = export_regression_triage_junit_xml(triage)
    # Parses despite special chars, and raw ampersand is escaped.
    root = ET.fromstring(xml)
    case = next(tc for tc in root.iter("testcase") if tc.get("name") == "x&y")
    assert "a < b & c > d" in case.find("failure").get("message")
    assert "&amp;" in xml


def test_junit_has_no_timestamps() -> None:
    xml = export_regression_triage_junit_xml(_mixed_triage())
    assert "timestamp" not in xml
    assert "2026" not in xml


def test_junit_legacy_report_does_not_crash() -> None:
    # No case_results -> aggregate summary testcase; still valid XML.
    triage = RegressionTriageEngine().compare_reports(
        {"pack": "p"}, {"pack": "p"}, TriagePolicy()
    )
    root = ET.fromstring(export_regression_triage_junit_xml(triage))
    cases = root.find("testsuite").findall("testcase")
    assert len(cases) == 1
    assert cases[0].get("name") == "regression-summary"


def test_junit_writer_matches_exporter(tmp_path) -> None:
    triage = _mixed_triage()
    path = tmp_path / "out" / "junit.xml"
    write_regression_triage_junit_xml(triage, path)
    assert path.exists()
    assert path.read_text() == export_regression_triage_junit_xml(triage)
