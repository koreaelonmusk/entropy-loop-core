"""Tests for the rule-based verifier."""

from __future__ import annotations

from entropy_loop_core import Verifier, require_contains


def test_default_verifier_rejects_empty_output() -> None:
    result = Verifier().verify("")
    assert not result.ok
    assert result.error == "output is empty"


def test_default_verifier_rejects_whitespace_only() -> None:
    assert not Verifier().verify("   \n\t").ok


def test_default_verifier_accepts_non_empty() -> None:
    result = Verifier().verify("hello")
    assert result.ok
    assert result.error is None


def test_require_contains_rule() -> None:
    verifier = Verifier(rules=[require_contains("ok")])
    assert verifier.verify("all ok here").ok
    assert not verifier.verify("nothing").ok


def test_first_failing_rule_short_circuits() -> None:
    verifier = Verifier()
    verifier.add_rule(require_contains("needle"))
    # Empty output fails the non-empty rule before the contains rule runs.
    result = verifier.verify("")
    assert result.error == "output is empty"
