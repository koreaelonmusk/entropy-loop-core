"""Tests for the self-contained HTML report (Pixel Failure Console)."""

from __future__ import annotations

from entropy_loop_core import (
    RegressionTriageEngine,
    TriagePolicy,
    export_regression_triage_html,
    write_regression_triage_html,
)


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
            {"case": c, "status": s, "message": m}
            for c, (s, m) in sorted(cases.items())
        ],
    }


def _triage():
    base = _report(
        "p", {"a": ("passed", None), "b": ("failed", "boom"), "c": ("passed", None)}
    )
    curr = _report(
        "p", {"a": ("failed", "broke"), "b": ("failed", "boom"), "c": ("passed", None)}
    )
    return RegressionTriageEngine().compare_reports(base, curr, TriagePolicy())


def test_html_has_title_and_subtitle() -> None:
    html = export_regression_triage_html(_triage())
    assert "Entropy Loop Failure Console" in html
    assert "AI agent regressions as CI evidence" in html


def test_html_is_deterministic() -> None:
    assert export_regression_triage_html(_triage()) == export_regression_triage_html(
        _triage()
    )


def test_html_escapes_special_characters() -> None:
    base = _report("p", {"a": ("passed", None)})
    curr = _report("p", {"a": ("failed", "a < b & c > d")})
    triage = RegressionTriageEngine().compare_reports(base, curr)
    html = export_regression_triage_html(triage)
    assert "&amp;" in html
    assert "&lt; b" in html
    assert "a < b & c > d" not in html  # raw not present


def test_html_has_no_timestamps() -> None:
    html = export_regression_triage_html(_triage())
    assert "2026" not in html


def test_html_has_no_external_resources() -> None:
    html = export_regression_triage_html(_triage())
    assert "http://" not in html
    assert "https://" not in html
    assert "//cdn" not in html.lower()


def test_html_has_no_external_scripts_or_styles() -> None:
    html = export_regression_triage_html(_triage())
    assert "<script" not in html.lower()
    assert 'rel="stylesheet"' not in html.lower()
    assert "<link" not in html.lower()


def test_html_has_summary_cards() -> None:
    html = export_regression_triage_html(_triage())
    assert "New failures" in html
    assert "Persistent failures" in html
    assert "Resolved" in html
    assert "Total cases" in html


def test_html_lists_new_and_persistent_and_resolved() -> None:
    base = _report(
        "p", {"a": ("passed", None), "b": ("failed", "boom"), "c": ("failed", "old")}
    )
    curr = _report(
        "p", {"a": ("failed", "broke"), "b": ("failed", "boom"), "c": ("passed", None)}
    )
    html = export_regression_triage_html(
        RegressionTriageEngine().compare_reports(base, curr)
    )
    assert "New Failures" in html and "a" in html  # a newly failing
    assert "Persistent Failures" in html  # b
    assert "Resolved Cases" in html  # c


def test_html_has_junit_semantics_note() -> None:
    html = export_regression_triage_html(_triage())
    assert "JUnit failures indicate reported regression/test state" in html


def test_html_writer_matches_exporter(tmp_path) -> None:
    triage = _triage()
    path = tmp_path / "out" / "report.html"
    write_regression_triage_html(triage, path)
    assert path.exists()
    assert path.read_text() == export_regression_triage_html(triage)
