"""Tests for the fluent, rule-based verifier and verification policy."""

from __future__ import annotations

from entropy_loop_core import AgentOutput, VerificationPolicy, Verifier


def _out(content: str) -> AgentOutput:
    return AgentOutput(content=content)


def test_require_non_empty_sets_category() -> None:
    result = Verifier().require_non_empty().verify(_out("   "))
    assert not result.passed
    assert result.rule_name == "non_empty_output"
    assert result.category == "empty_output"


def test_require_terms_reports_missing_in_details() -> None:
    verifier = Verifier().require_terms(["status", "id"])
    assert verifier.verify(_out("status id")).passed
    result = verifier.verify(_out("status only"))
    assert not result.passed
    assert result.category == "missing_required_term"
    assert result.details["missing"] == ["id"]


def test_expect_json_category() -> None:
    verifier = Verifier().expect_json()
    assert verifier.verify(_out('{"ok": true}')).passed
    result = verifier.verify(_out("not json"))
    assert not result.passed
    assert result.category == "invalid_json"


def test_max_length_category_and_details() -> None:
    verifier = Verifier().max_length(5)
    assert verifier.verify(_out("short")).passed
    result = verifier.verify(_out("far too long"))
    assert not result.passed
    assert result.category == "too_long"
    assert result.severity == "warning"
    assert result.details == {"length": 12, "limit": 5}


def test_first_failing_rule_wins() -> None:
    verifier = Verifier().require_non_empty().require_terms(["status"])
    result = verifier.verify(_out(""))
    assert result.rule_name == "non_empty_output"


def test_empty_verifier_passes_everything() -> None:
    assert Verifier().verify(_out("")).passed


def test_from_policy_builds_configured_verifier() -> None:
    policy = VerificationPolicy(
        require_non_empty=True, required_terms=["status"], max_length=100
    )
    verifier = Verifier.from_policy(policy)

    assert verifier.verify(_out("status: ok")).passed
    # Missing the required term fails after passing the non-empty check.
    assert verifier.verify(_out("done")).category == "missing_required_term"
    # Empty fails on the first rule.
    assert verifier.verify(_out("")).category == "empty_output"


def test_from_policy_default_is_permissive() -> None:
    assert Verifier.from_policy(VerificationPolicy()).verify(_out("")).passed
