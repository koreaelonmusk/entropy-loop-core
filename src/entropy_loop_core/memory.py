"""In-memory storage for failures and lessons.

:class:`MemoryStore` is the simplest possible persistence layer: it keeps
records in process memory. It gives agents a place to remember what went wrong
and what was learned, which higher layers can later swap for a durable backend.
"""

from __future__ import annotations

from .types import Failure, Lesson


class MemoryStore:
    """Simple in-memory store for failures and lessons.

    The store is deliberately minimal. It accumulates :class:`Failure` and
    :class:`Lesson` records and exposes read helpers for inspection. It is not
    thread-safe and holds no state beyond the current process.
    """

    def __init__(self) -> None:
        """Initialize an empty store."""
        self._failures: list[Failure] = []
        self._lessons: list[Lesson] = []

    def record_failure(self, failure: Failure) -> None:
        """Persist a failure record.

        Args:
            failure: The failure to remember.
        """
        self._failures.append(failure)

    def record_lesson(self, lesson: Lesson) -> None:
        """Persist a lesson record.

        Args:
            lesson: The lesson to remember.
        """
        self._lessons.append(lesson)

    def failures(self) -> list[Failure]:
        """Return all recorded failures in insertion order."""
        return list(self._failures)

    def lessons(self) -> list[Lesson]:
        """Return all recorded lessons in insertion order."""
        return list(self._lessons)

    def failures_for(self, task_prompt: str) -> list[Failure]:
        """Return recorded failures matching a given task prompt.

        Args:
            task_prompt: The prompt to filter failures by.

        Returns:
            Failures whose ``task_prompt`` equals the given value.
        """
        return [f for f in self._failures if f.task_prompt == task_prompt]

    def clear(self) -> None:
        """Remove all stored failures and lessons."""
        self._failures.clear()
        self._lessons.clear()
