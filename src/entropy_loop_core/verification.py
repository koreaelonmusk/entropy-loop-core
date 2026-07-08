"""Rule-based verification of agent outputs.

:class:`Verifier` applies an ordered list of small, composable rules to an
:class:`~entropy_loop_core.types.AgentOutput` and reports the first violation.
Each rule is a plain callable that returns a
:class:`~entropy_loop_core.types.VerificationResult`, so callers can extend
verification without subclassing.

The rules here are deterministic and do no I/O — no network, no model calls.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable

from .types import AgentOutput, Severity, Task, VerificationResult

# A rule inspects a task and its output and returns a verdict.
Rule = Callable[[Task, AgentOutput], VerificationResult]


def _passed(rule_name: str) -> VerificationResult:
    """Return a passing result for the named rule."""
    return VerificationResult(passed=True, rule_name=rule_name)


def non_empty_output(severity: Severity = Severity.ERROR) -> Rule:
    """Build a rule that fails on empty or whitespace-only output.

    Args:
        severity: Severity to report on failure.

    Returns:
        A :data:`Rule` enforcing a non-empty output.
    """
    name = "non_empty_output"

    def rule(task: Task, output: AgentOutput) -> VerificationResult:
        if not output.content or not output.content.strip():
            return VerificationResult(
                passed=False,
                reason="output is empty",
                rule_name=name,
                severity=severity,
            )
        return _passed(name)

    return rule


def contains_required_terms(
    terms: Iterable[str], severity: Severity = Severity.ERROR
) -> Rule:
    """Build a rule requiring every term in ``terms`` to appear in the output.

    Args:
        terms: Substrings that must all be present.
        severity: Severity to report on failure.

    Returns:
        A :data:`Rule` enforcing the containment check.
    """
    required = list(terms)
    name = "contains_required_terms"

    def rule(task: Task, output: AgentOutput) -> VerificationResult:
        missing = [term for term in required if term not in output.content]
        if missing:
            return VerificationResult(
                passed=False,
                reason=f"missing required terms: {missing}",
                rule_name=name,
                severity=severity,
            )
        return _passed(name)

    return rule


def valid_json_when_expected(
    metadata_key: str = "expected_format",
    expected_value: str = "json",
    severity: Severity = Severity.ERROR,
) -> Rule:
    """Build a rule that requires valid JSON only when the task asks for it.

    The rule passes trivially unless ``task.metadata[metadata_key]`` equals
    ``expected_value`` (default: ``expected_format == "json"``). When JSON is
    expected, the output content must parse as JSON.

    Args:
        metadata_key: Task metadata key that signals the expected format.
        expected_value: Value of that key that requires JSON.
        severity: Severity to report on failure.

    Returns:
        A :data:`Rule` enforcing conditional JSON validity.
    """
    name = "valid_json_when_expected"

    def rule(task: Task, output: AgentOutput) -> VerificationResult:
        if task.metadata.get(metadata_key) != expected_value:
            return _passed(name)
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

    return rule


def max_length(limit: int, severity: Severity = Severity.WARNING) -> Rule:
    """Build a rule that fails when output exceeds ``limit`` characters.

    Args:
        limit: Maximum allowed length of the output content.
        severity: Severity to report on failure (defaults to a warning).

    Returns:
        A :data:`Rule` enforcing the length bound.
    """
    name = "max_length"

    def rule(task: Task, output: AgentOutput) -> VerificationResult:
        if len(output.content) > limit:
            return VerificationResult(
                passed=False,
                reason=f"output exceeds {limit} characters",
                rule_name=name,
                severity=severity,
            )
        return _passed(name)

    return rule


class Verifier:
    """Validates agent outputs against an ordered list of rules.

    By default the verifier requires a non-empty output. Rules run in order and
    the first failure short-circuits the check.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        """Create a verifier.

        Args:
            rules: Rules to apply. When ``None``, a single non-empty check is
                used.
        """
        self._rules: list[Rule] = rules if rules is not None else [non_empty_output()]

    def add_rule(self, rule: Rule) -> None:
        """Append a rule to the verifier.

        Args:
            rule: A callable returning a :class:`VerificationResult`.
        """
        self._rules.append(rule)

    def verify(self, task: Task, output: AgentOutput) -> VerificationResult:
        """Verify an output against every rule.

        Args:
            task: The task the output was produced for.
            output: The agent output to validate.

        Returns:
            The first failing :class:`VerificationResult`, or a passing result
            named ``"all"`` when every rule passed.
        """
        for rule in self._rules:
            result = rule(task, output)
            if not result.passed:
                return result
        return VerificationResult(passed=True, rule_name="all")
