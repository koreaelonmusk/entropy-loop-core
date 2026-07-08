"""Entropy Loop Core.

An open-source *Failure Compiler* for AI agents. It turns bad outputs into
structured failure traces, compiles those traces into reusable lessons, retries
with improved context, and generates regression cases so the same failure does
not happen twice.

The public API is intentionally small:

- Data contract — :class:`Task`, :class:`AgentOutput`, :class:`VerificationResult`,
  :class:`FailureTrace`, :class:`Lesson`, :class:`RegressionCase`,
  :class:`AgentContext`, :class:`LoopResult`, :class:`LoopStatus`, :class:`Severity`.
- :class:`MemoryStore` — in-memory failure/lesson storage with lesson recall.
- :class:`Verifier` and rule builders — rule-based output validation.
- :class:`LessonGenerator` — deterministic failure-to-lesson compilation.
- :class:`RegressionGenerator` — failure-to-regression-case generation.
- :class:`EntropyLoop` — run, verify, trace, learn, retry.
"""

from __future__ import annotations

from .lessons import LessonGenerator
from .loop import Agent, EntropyLoop
from .memory import MemoryStore
from .regression import RegressionGenerator
from .types import (
    AgentContext,
    AgentOutput,
    FailureTrace,
    Lesson,
    LoopResult,
    LoopStatus,
    RegressionCase,
    Severity,
    Task,
    VerificationResult,
)
from .verification import (
    Rule,
    Verifier,
    contains_required_terms,
    max_length,
    non_empty_output,
    valid_json_when_expected,
)

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "AgentContext",
    "AgentOutput",
    "EntropyLoop",
    "FailureTrace",
    "Lesson",
    "LessonGenerator",
    "LoopResult",
    "LoopStatus",
    "MemoryStore",
    "RegressionCase",
    "RegressionGenerator",
    "Rule",
    "Severity",
    "Task",
    "VerificationResult",
    "Verifier",
    "contains_required_terms",
    "max_length",
    "non_empty_output",
    "valid_json_when_expected",
    "__version__",
]
