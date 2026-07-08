"""Summarizing a loop run.

:func:`summarize` rolls a :class:`~entropy_loop_core.types.LoopResult` up into a
compact :class:`~entropy_loop_core.types.EvaluationSummary` so developers can see
what happened after a run: how many attempts, whether it succeeded, and how the
failures break down by category.

It is deterministic and side-effect free — **no dashboards, no charts, no
telemetry, nothing phones home**.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from .types import EvaluationSummary, LoopResult, RegressionCase


def summarize(
    result: LoopResult, regression_cases: Sequence[RegressionCase] = ()
) -> EvaluationSummary:
    """Summarize a loop run into an :class:`EvaluationSummary`.

    Args:
        result: The result of an :class:`~entropy_loop_core.loop.EntropyLoop`
            run.
        regression_cases: Any regression cases generated from the run's
            failures; only their count is recorded.

    Returns:
        A compact, public-safe :class:`EvaluationSummary`.
    """
    categories = Counter(trace.category for trace in result.failures)
    return EvaluationSummary(
        total_attempts=result.attempts,
        success=result.status == "success",
        failure_count=len(result.failures),
        categories=dict(categories),
        final_status=result.status,
        generated_regression_cases=len(regression_cases),
    )
