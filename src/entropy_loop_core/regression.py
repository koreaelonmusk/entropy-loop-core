"""Generating regression cases from failures.

:class:`RegressionGenerator` turns a
:class:`~entropy_loop_core.types.FailureTrace` into a
:class:`~entropy_loop_core.types.RegressionCase`: a small, test-like artifact
that pins down a task which once failed and the rule that must pass for it to be
considered fixed. This closes the loop — a failure is not just remembered, it
becomes something you can check forever.
"""

from __future__ import annotations

import re

from .types import FailureTrace, RegressionCase


def _slugify(text: str, max_len: int = 40) -> str:
    """Turn arbitrary text into a lowercase, identifier-friendly slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:max_len] or "case"


class RegressionGenerator:
    """Generates regression cases from failure traces.

    The generator is deterministic and side-effect free. It names each case
    from the task and failed rule so repeated failures map to stable names.
    """

    def generate(self, trace: FailureTrace) -> RegressionCase:
        """Generate a regression case from a single failure trace.

        Args:
            trace: The structured failure to turn into a regression case.

        Returns:
            A :class:`RegressionCase` capturing the task, the rule that must
            pass, and the original failure reason.
        """
        rule_name = trace.verification_result.rule_name or "unknown"
        name = f"regression_{_slugify(trace.task.instruction)}_{rule_name}"
        return RegressionCase(
            name=name,
            instruction=trace.task.instruction,
            expected_rule=rule_name,
            failure_reason=trace.verification_result.reason or "verification failed",
        )
