"""Generating regression cases from failures.

:func:`generate_regression_case` turns a
:class:`~entropy_loop_core.types.FailureTrace` into a
:class:`~entropy_loop_core.types.RegressionCase`: a small, test-like artifact
that pins down a task which once failed and the rule that must pass for it to be
considered fixed. This closes the loop — a failure is not just remembered, it
becomes something you can check later.

The function is deterministic and side-effect free, and produces only generic,
public-safe artifacts.
"""

from __future__ import annotations

import re

from .types import FailureTrace, RegressionCase


def _slugify(text: str, max_len: int = 40) -> str:
    """Turn arbitrary text into a lowercase, identifier-friendly slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:max_len] or "case"


def generate_regression_case(trace: FailureTrace) -> RegressionCase:
    """Generate a regression case from a single failure trace.

    The case is named from the task and the failed rule so that repeated
    failures map to a stable name.

    Args:
        trace: The structured failure to turn into a regression case.

    Returns:
        A :class:`RegressionCase` capturing the task, the rule that must pass,
        and the original failure reason.
    """
    rule_name = trace.verification_result.rule_name or "unknown"
    name = f"regression_{_slugify(trace.task.instruction)}_{rule_name}"
    return RegressionCase(
        name=name,
        instruction=trace.task.instruction,
        expected_rule=rule_name,
        failure_reason=trace.verification_result.reason or "verification failed",
    )
