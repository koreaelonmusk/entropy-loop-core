"""Entropy Loop Core.

An open-source *Failure Compiler* for AI agents. It captures bad outputs as
structured failure traces, **classifies** them, compiles them into reusable
lessons, retries with improved context, generates regression cases so the same
failure does not happen twice, and summarizes the run.

The public API is intentionally small:

- Data contract — :class:`Task`, :class:`AgentOutput`, :class:`VerificationResult`,
  :class:`FailureTrace`, :class:`Lesson`, :class:`RetryContext`,
  :class:`LoopResult`, :class:`RegressionCase`, :class:`EvaluationSummary`, and
  the ``Severity`` / ``Status`` / ``FailureCategory`` literals.
- :class:`MemoryStore` — in-memory failure/lesson storage with lesson recall.
- :class:`Verifier` / :class:`VerificationPolicy` — rule-based validation.
- :class:`LessonGenerator` — deterministic, category-based lesson compilation.
- :func:`generate_regression_case` / :func:`export_regression_cases` — regression
  case generation and export.
- :func:`summarize` — roll a run up into an :class:`EvaluationSummary`.
- :class:`EntropyLoop` — run, verify, classify, trace, learn, retry.
"""

from __future__ import annotations

from .evaluation import summarize
from .lessons import LessonGenerator
from .loop import Agent, EntropyLoop
from .memory import MemoryStore
from .regression import (
    export_regression_case,
    export_regression_cases,
    generate_regression_case,
)
from .types import (
    AgentOutput,
    EvaluationSummary,
    FailureCategory,
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
from .verification import Rule, VerificationPolicy, Verifier

__version__ = "0.2.0"

__all__ = [
    "Agent",
    "AgentOutput",
    "EntropyLoop",
    "EvaluationSummary",
    "FailureCategory",
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
    "VerificationPolicy",
    "VerificationResult",
    "Verifier",
    "export_regression_case",
    "export_regression_cases",
    "generate_regression_case",
    "summarize",
    "__version__",
]
