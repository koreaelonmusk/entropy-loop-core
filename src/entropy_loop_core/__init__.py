"""Entropy Loop Core.

An open-source reliability layer for AI agents. It helps agents remember
failures, verify outputs, and improve through feedback loops.

The public API is intentionally small:

- :class:`Task`, :class:`LoopResult`, :class:`LoopStatus`, :class:`Failure`,
  :class:`Lesson` — typed data objects.
- :class:`MemoryStore` — in-memory failure/lesson storage.
- :class:`Verifier` — rule-based output validation.
- :class:`EntropyLoop` — run, verify, remember, retry.
"""

from __future__ import annotations

from .loop import Agent, EntropyLoop
from .memory import MemoryStore
from .types import Failure, Lesson, LoopResult, LoopStatus, Task
from .verification import Rule, VerificationResult, Verifier, require_contains

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "EntropyLoop",
    "Failure",
    "Lesson",
    "LoopResult",
    "LoopStatus",
    "MemoryStore",
    "Rule",
    "Task",
    "VerificationResult",
    "Verifier",
    "require_contains",
    "__version__",
]
