"""Tests for the rule-based verifier."""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    Severity,
    Task,
    Verifier,
    contains_required_terms,
    max_length,
    non_empty_output,
    valid_json_when_expected,
)


def _out(content: str) -> AgentOutput:
    return AgentOutput(content=content)


TASK = Task(instruction="do the thing")


def test_default_verifier_rejects_empty_output() -> None:
    result = Verifier().verify(TASK, _out(""))
    assert not result.passed
    assert result.reason == "output is empty"
    assert result.rule_name == "non_empty_output"


def test_default_verifier_rejects_whitespace_only() -> None:
    assert not Verifier().verify(TASK, _out("  \n\t")).passed


def test_default_verifier_accepts_non_empty() -> None:
    result = Verifier().verify(TASK, _out("hello"))
    assert result.passed
    assert result.reason is None
    assert result.rule_name == "all"


def test_contains_required_terms_reports_missing() -> None:
    verifier = Verifier(rules=[contains_required_terms(["alpha", "beta"])])
    assert verifier.verify(TASK, _out("alpha and beta")).passed
    result = verifier.verify(TASK, _out("only alpha"))
    assert not result.passed
    assert "beta" in result.reason


def test_valid_json_only_enforced_when_expected() -> None:
    rule = valid_json_when_expected()
    plain = Verifier(rules=[rule])
    # Not expecting JSON -> any content passes.
    assert plain.verify(Task(instruction="x"), _out("not json")).passed

    json_task = Task(instruction="x", metadata={"expected_format": "json"})
    assert plain.verify(json_task, _out('{"ok": true}')).passed
    assert not plain.verify(json_task, _out("not json")).passed


def test_max_length_rule_and_severity() -> None:
    verifier = Verifier(rules=[max_length(5)])
    assert verifier.verify(TASK, _out("short")).passed
    result = verifier.verify(TASK, _out("way too long"))
    assert not result.passed
    assert result.severity is Severity.WARNING


def test_custom_severity_is_reported() -> None:
    verifier = Verifier(rules=[non_empty_output(severity=Severity.CRITICAL)])
    result = verifier.verify(TASK, _out(""))
    assert result.severity is Severity.CRITICAL


def test_first_failing_rule_short_circuits() -> None:
    verifier = Verifier()
    verifier.add_rule(contains_required_terms(["needle"]))
    # Empty output fails the non-empty rule before the contains rule runs.
    result = verifier.verify(TASK, _out(""))
    assert result.rule_name == "non_empty_output"
