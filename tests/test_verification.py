"""Tests for the fluent, rule-based verifier."""

from __future__ import annotations

from entropy_loop_core import AgentOutput, Verifier


def _out(content: str) -> AgentOutput:
    return AgentOutput(content=content)


def test_require_non_empty_rejects_blank() -> None:
    result = Verifier().require_non_empty().verify(_out("   "))
    assert not result.passed
    assert result.rule_name == "non_empty_output"
    assert result.reason == "output is empty"


def test_require_non_empty_accepts_content() -> None:
    result = Verifier().require_non_empty().verify(_out("hello"))
    assert result.passed
    assert result.rule_name == "all"


def test_require_terms_reports_missing() -> None:
    verifier = Verifier().require_terms(["status"])
    assert verifier.verify(_out("status: ok")).passed
    result = verifier.verify(_out("done"))
    assert not result.passed
    assert "status" in result.reason


def test_expect_json() -> None:
    verifier = Verifier().expect_json()
    assert verifier.verify(_out('{"ok": true}')).passed
    assert not verifier.verify(_out("not json")).passed


def test_max_length_is_a_warning() -> None:
    verifier = Verifier().max_length(5)
    assert verifier.verify(_out("short")).passed
    result = verifier.verify(_out("far too long"))
    assert not result.passed
    assert result.severity == "warning"


def test_first_failing_rule_wins() -> None:
    # Non-empty is added first, so an empty output fails on it, not on terms.
    verifier = Verifier().require_non_empty().require_terms(["status"])
    result = verifier.verify(_out(""))
    assert result.rule_name == "non_empty_output"


def test_empty_verifier_passes_everything() -> None:
    assert Verifier().verify(_out("")).passed


def test_fluent_chaining_returns_verifier() -> None:
    verifier = Verifier().require_non_empty().require_terms(["x"]).max_length(100)
    assert isinstance(verifier, Verifier)
