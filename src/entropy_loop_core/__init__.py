"""Entropy Loop Core.

An open-source *Failure Compiler* for AI agents. It turns bad outputs into
structured failure traces, compiles those traces into reusable lessons, retries
with improved context, and generates regression cases so the same failure does
not happen twice.

The public API is intentionally small:

- Data contract — :class:`Task`, :class:`AgentOutput`, :class:`VerificationResult`,
  :class:`FailureTrace`, :class:`Lesson`, :class:`RetryContext`,
  :class:`LoopResult`, :class:`RegressionCase`, and the ``Severity``/``Status``
  literals.
- :class:`MemoryStore` — in-memory failure/lesson storage with lesson recall.
- :class:`Verifier` — fluent, rule-based output validation.
- :class:`LessonGenerator` — deterministic failure-to-lesson compilation.
- :func:`generate_regression_case` — failure-to-regression-case generation.
- :class:`EntropyLoop` — run, verify, trace, learn, retry.
"""

from __future__ import annotations

from .lessons import LessonGenerator
from .loop import Agent, EntropyLoop
from .memory import MemoryStore
from .regression import generate_regression_case
from .types import (
    AgentOutput,
    FailureTrace,
    Lesson,
    LoopResult,
    RegressionCase,
    RetryContext,
    Severity,
    Status,
    Task,
    VerificationResult,
)
from .verification import Rule, Verifier

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "AgentOutput",
    "EntropyLoop",
    "FailureTrace",
    "Lesson",
    "LessonGenerator",
    "LoopResult",
    "MemoryStore",
    "RegressionCase",
    "RetryContext",
    "Rule",
    "Severity",
    "Status",
    "Task",
    "VerificationResult",
    "Verifier",
    "generate_regression_case",
    "__version__",
]
