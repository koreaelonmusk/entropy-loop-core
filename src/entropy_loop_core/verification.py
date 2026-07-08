"""Rule-based verification of agent outputs.

:class:`Verifier` applies a list of small, composable rules to an agent output
and reports the first violation it finds. Rules are plain callables, so callers
can extend verification without subclassing.
"""

from __future__ import annotations

from collections.abc import Callable

# A rule inspects an output and returns an error message when the output is
# invalid, or ``None`` when the output passes.
Rule = Callable[[str], str | None]


class VerificationResult:
    """Outcome of verifying a single agent output.

    Attributes:
        ok: ``True`` when every rule passed.
        error: The first violation message, or ``None`` when ``ok`` is ``True``.
    """

    def __init__(self, ok: bool, error: str | None = None) -> None:
        """Create a verification result.

        Args:
            ok: Whether verification passed.
            error: The violation message when verification failed.
        """
        self.ok = ok
        self.error = error

    def __repr__(self) -> str:  # pragma: no cover - trivial
        """Return a debug representation of the result."""
        return f"VerificationResult(ok={self.ok!r}, error={self.error!r})"


def non_empty_rule(output: str) -> str | None:
    """Fail when the output is empty or whitespace-only."""
    if not output or not output.strip():
        return "output is empty"
    return None


class Verifier:
    """Validates agent outputs against a set of rules.

    By default the verifier requires a non-empty output. Additional rules may
    be supplied to enforce domain-specific expectations.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        """Create a verifier.

        Args:
            rules: Rules to apply. When ``None``, a single non-empty check is
                used.
        """
        self._rules: list[Rule] = rules if rules is not None else [non_empty_rule]

    def add_rule(self, rule: Rule) -> None:
        """Append a rule to the verifier.

        Args:
            rule: A callable returning an error message on failure, else ``None``.
        """
        self._rules.append(rule)

    def verify(self, output: str) -> VerificationResult:
        """Verify an output against all rules.

        Rules run in order; the first failure short-circuits the check.

        Args:
            output: The agent output to validate.

        Returns:
            A :class:`VerificationResult` describing the outcome.
        """
        for rule in self._rules:
            error = rule(output)
            if error is not None:
                return VerificationResult(ok=False, error=error)
        return VerificationResult(ok=True)


def require_contains(substring: str) -> Rule:
    """Build a rule that requires ``substring`` to appear in the output.

    Args:
        substring: The text that must be present.

    Returns:
        A :data:`Rule` enforcing the containment check.
    """

    def rule(output: str) -> str | None:
        if substring not in output:
            return f"output must contain {substring!r}"
        return None

    return rule
