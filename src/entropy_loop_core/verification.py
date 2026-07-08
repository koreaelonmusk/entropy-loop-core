"""Deterministic, rule-based verification of agent outputs.

:class:`Verifier` collects a small set of simple, composable rules and applies
them in order to an :class:`~entropy_loop_core.types.AgentOutput`. The API is a
fluent builder::

    verifier = Verifier()
    verifier.require_non_empty()
    verifier.require_terms(["status"])
    verifier.expect_json()
    verifier.max_length(500)
    result = verifier.verify(output)

Rules are deterministic and do no I/O — no network, no model calls. If several
rules would fail, :meth:`Verifier.verify` returns the first failure (v0.1.0).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable

from .types import AgentOutput, Severity, VerificationResult

# A rule inspects an output and returns a verdict.
Rule = Callable[[AgentOutput], VerificationResult]


def _passed(rule_name: str) -> VerificationResult:
    """Return a passing result for the named rule."""
    return VerificationResult(passed=True, rule_name=rule_name, severity="info")


class Verifier:
    """Validates agent outputs against an ordered list of simple rules.

    Rules are added with the fluent ``require_*`` / ``expect_*`` / ``max_length``
    methods and applied in the order they were added. A fresh verifier with no
    rules passes every output; call at least one rule method to make it useful.
    """

    def __init__(self) -> None:
        """Create a verifier with no rules."""
        self._rules: list[Rule] = []

    def require_non_empty(self, severity: Severity = "error") -> Verifier:
        """Require the output to be non-empty (ignoring whitespace).

        Args:
            severity: Severity to report on failure.

        Returns:
            This verifier, for chaining.
        """
        name = "non_empty_output"

        def rule(output: AgentOutput) -> VerificationResult:
            if not output.content or not output.content.strip():
                return VerificationResult(
                    passed=False,
                    reason="output is empty",
                    rule_name=name,
                    severity=severity,
                )
            return _passed(name)

        self._rules.append(rule)
        return self

    def require_terms(
        self, terms: Iterable[str], severity: Severity = "error"
    ) -> Verifier:
        """Require every term in ``terms`` to appear in the output.

        Args:
            terms: Substrings that must all be present.
            severity: Severity to report on failure.

        Returns:
            This verifier, for chaining.
        """
        required = list(terms)
        name = "contains_required_terms"

        def rule(output: AgentOutput) -> VerificationResult:
            missing = [term for term in required if term not in output.content]
            if missing:
                return VerificationResult(
                    passed=False,
                    reason=f"missing required terms: {missing}",
                    rule_name=name,
                    severity=severity,
                )
            return _passed(name)

        self._rules.append(rule)
        return self

    def expect_json(self, severity: Severity = "error") -> Verifier:
        """Require the output content to parse as valid JSON.

        Args:
            severity: Severity to report on failure.

        Returns:
            This verifier, for chaining.
        """
        name = "valid_json_when_expected"

        def rule(output: AgentOutput) -> VerificationResult:
            try:
                json.loads(output.content)
            except (json.JSONDecodeError, ValueError) as exc:
                return VerificationResult(
                    passed=False,
                    reason=f"expected valid JSON: {exc}",
                    rule_name=name,
                    severity=severity,
                )
            return _passed(name)

        self._rules.append(rule)
        return self

    def max_length(self, limit: int, severity: Severity = "warning") -> Verifier:
        """Require the output to be at most ``limit`` characters.

        Args:
            limit: Maximum allowed length of the output content.
            severity: Severity to report on failure (defaults to a warning).

        Returns:
            This verifier, for chaining.
        """
        name = "max_length"

        def rule(output: AgentOutput) -> VerificationResult:
            if len(output.content) > limit:
                return VerificationResult(
                    passed=False,
                    reason=f"output exceeds {limit} characters",
                    rule_name=name,
                    severity=severity,
                )
            return _passed(name)

        self._rules.append(rule)
        return self

    def verify(self, output: AgentOutput) -> VerificationResult:
        """Verify an output against every configured rule, in order.

        Args:
            output: The agent output to validate.

        Returns:
            The first failing :class:`VerificationResult`, or a passing result
            named ``"all"`` when every rule passed.
        """
        for rule in self._rules:
            result = rule(output)
            if not result.passed:
                return result
        return VerificationResult(passed=True, rule_name="all", severity="info")
