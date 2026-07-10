"""Checks for the Action self-test workflow (v0.8.1 runner hardening)."""

from __future__ import annotations

from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "action-self-test.yml"
)


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_exists() -> None:
    assert WORKFLOW.is_file()


def test_least_privilege_permissions() -> None:
    assert "permissions:" in _text()
    assert "contents: read" in _text()


def test_uses_checkout_and_setup_python() -> None:
    text = _text()
    assert "actions/checkout@v4" in text
    assert "actions/setup-python@v5" in text


def test_local_action_uses_dot_slash() -> None:
    assert "uses: ./" in _text()


def test_local_action_avoids_pypi() -> None:
    # The local Action self-test must not reinstall from PyPI.
    assert "install-package: false" in _text()


def test_invokes_write_ci_evidence_or_action() -> None:
    text = _text()
    # Either via the composite Action (uses: ./) or the CLI policy job.
    assert "entropy-loop write-ci-evidence" in text
    assert "entropy-loop ci-demo" in text


def test_exit_codes_asserted() -> None:
    text = _text()
    assert 'test "$code" -eq 1' in text
    assert 'test "$code" -eq 0' in text
    assert 'test "$code" -eq 2' in text


def test_no_token_or_api_or_curl() -> None:
    text = _text().lower()
    assert "github_token" not in text
    assert "gh api" not in text
    assert "curl" not in text


def test_no_write_permissions() -> None:
    text = _text()
    assert "pull-requests: write" not in text
    assert "issues: write" not in text
    assert "id-token: write" not in text
    assert "packages: write" not in text


def test_workflow_exercises_junit() -> None:
    text = _text()
    # The local Action self-test requests a JUnit report and verifies it parses.
    assert "junit-report: reports/entropy-loop-junit.xml" in text
    assert "reports/entropy-loop-junit.xml" in text
    assert "xml.etree.ElementTree" in text


def test_workflow_exercises_html() -> None:
    text = _text()
    # The local Action self-test requests an HTML report and verifies it.
    assert "html-report: reports/entropy-loop.html" in text
    assert "Entropy Loop Failure Console" in text
    assert "AI agent regressions as CI evidence" in text
    assert "JUnit failures indicate reported regression/test state" in text


def test_workflow_html_verify_checks_no_external() -> None:
    text = _text()
    assert '! grep -q "http://" reports/entropy-loop.html' in text
    assert '! grep -q "https://" reports/entropy-loop.html' in text


def test_workflow_sets_html_locale() -> None:
    assert "html-locale: en" in _text()


def test_workflow_checks_korean_html() -> None:
    text = _text()
    assert "--html-locale ko" in text
    assert "엔트로피 루프 실패 콘솔" in text
    assert "AI 에이전트 회귀를 CI 증거로 변환" in text
