"""Generating and exporting regression cases from failures.

:func:`generate_regression_case` turns a
:class:`~entropy_loop_core.types.FailureTrace` into a
:class:`~entropy_loop_core.types.RegressionCase`: a small, test-like artifact
that pins down a task which once failed and the rule that must pass for it to be
considered fixed. :func:`export_regression_case` / :func:`export_regression_cases`
render cases as plain dictionaries for serialization.

All functions are deterministic and side-effect free, and produce only generic,
public-safe artifacts.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .types import FailureTrace, RegressionCase, RegressionReport, RegressionSuite


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
        the original failure reason, and the failure category.
    """
    result = trace.verification_result
    rule_name = result.rule_name or "unknown"
    name = f"regression_{_slugify(trace.task.instruction)}_{rule_name}"
    return RegressionCase(
        name=name,
        instruction=trace.task.instruction,
        expected_rule=rule_name,
        failure_reason=result.reason or "verification failed",
        category=result.category,
    )


def export_regression_case(case: RegressionCase) -> dict[str, Any]:
    """Render a regression case as a plain, serializable dictionary.

    Args:
        case: The regression case to export.

    Returns:
        A dictionary of the case's fields.
    """
    return case.model_dump()


def export_regression_cases(cases: Iterable[RegressionCase]) -> list[dict[str, Any]]:
    """Render a collection of regression cases as plain dictionaries.

    Args:
        cases: The regression cases to export.

    Returns:
        A list of dictionaries, one per case, in order.
    """
    return [export_regression_case(case) for case in cases]


def export_regression_suite(suite: RegressionSuite) -> dict[str, Any]:
    """Render a regression suite as a plain, JSON-compatible dictionary."""
    return suite.model_dump()


def import_regression_suite(data: dict[str, Any]) -> RegressionSuite:
    """Build a regression suite from a plain dictionary.

    Args:
        data: A dictionary as produced by :func:`export_regression_suite`.

    Returns:
        The reconstructed :class:`RegressionSuite`.
    """
    return RegressionSuite.model_validate(data)


def export_regression_report(report: RegressionReport) -> dict[str, Any]:
    """Render a regression report as a plain, JSON-compatible dictionary."""
    return report.model_dump()


def save_regression_suite(suite: RegressionSuite, path: str | Path) -> None:
    """Write a regression suite to a local JSON file.

    Args:
        suite: The suite to save.
        path: Destination path on the local filesystem.
    """
    Path(path).write_text(
        json.dumps(export_regression_suite(suite), indent=2), encoding="utf-8"
    )


def load_regression_suite(path: str | Path) -> RegressionSuite:
    """Read a regression suite from a local JSON file.

    Args:
        path: Path to a JSON file produced by :func:`save_regression_suite`.

    Returns:
        The reconstructed :class:`RegressionSuite`.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return import_regression_suite(data)
