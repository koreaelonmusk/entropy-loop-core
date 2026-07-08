"""In-memory storage for failure traces and lessons.

:class:`MemoryStore` is the simplest possible persistence layer: it keeps
records in process memory. It gives the compiler somewhere to remember what
went wrong and what was learned, and a way to surface lessons relevant to a new
task. Higher layers can later swap it for a durable backend.
"""

from __future__ import annotations

import re

from .types import FailureTrace, Lesson, Task

# Tokens shorter than this, and common stopwords, are ignored when matching
# lessons to tasks so that overlap reflects meaningful shared terms.
_MIN_TOKEN_LEN = 3
_STOPWORDS = frozenset(
    {"the", "and", "for", "with", "that", "this", "from", "into", "your", "you"}
)


def _tokenize(text: str) -> set[str]:
    """Split text into a set of lowercase content-word tokens for matching."""
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= _MIN_TOKEN_LEN and token not in _STOPWORDS
    }


class MemoryStore:
    """In-memory store for failure traces and lessons.

    The store is deliberately minimal. It accumulates
    :class:`~entropy_loop_core.types.FailureTrace` and
    :class:`~entropy_loop_core.types.Lesson` records and exposes read helpers,
    including a lightweight relevance search over lessons. It is not thread-safe
    and holds no state beyond the current process.
    """

    def __init__(self) -> None:
        """Initialize an empty store."""
        self._failures: list[FailureTrace] = []
        self._lessons: list[Lesson] = []

    def add_failure(self, trace: FailureTrace) -> None:
        """Remember a failure trace.

        Args:
            trace: The structured failure to store.
        """
        self._failures.append(trace)

    def add_lesson(self, lesson: Lesson) -> None:
        """Remember a lesson.

        Args:
            lesson: The lesson to store.
        """
        self._lessons.append(lesson)

    def recent_failures(self, limit: int = 5) -> list[FailureTrace]:
        """Return the most recent failure traces.

        Args:
            limit: Maximum number of traces to return, newest last.

        Returns:
            Up to ``limit`` failure traces in insertion order.
        """
        if limit < 0:
            raise ValueError("limit must be non-negative")
        return self._failures[-limit:] if limit else []

    def relevant_lessons(self, task: Task, limit: int = 5) -> list[Lesson]:
        """Return lessons most relevant to ``task``.

        Relevance is a deterministic keyword overlap between the task
        (its instruction and metadata values) and each lesson (its summary and
        tags). When no lesson overlaps, the most recent lessons are returned so
        the loop always has some context to retry with.

        Args:
            task: The task to find lessons for.
            limit: Maximum number of lessons to return, most relevant last.

        Returns:
            Up to ``limit`` lessons.
        """
        if limit < 0:
            raise ValueError("limit must be non-negative")
        if not self._lessons or not limit:
            return []

        query = _tokenize(task.instruction)
        for value in task.metadata.values():
            query |= _tokenize(value)

        matched: list[Lesson] = []
        for lesson in self._lessons:
            haystack = _tokenize(lesson.summary) | {tag.lower() for tag in lesson.tags}
            if query & haystack:
                matched.append(lesson)

        pool = matched if matched else self._lessons
        return pool[-limit:]

    def failures(self) -> list[FailureTrace]:
        """Return all stored failure traces in insertion order."""
        return list(self._failures)

    def lessons(self) -> list[Lesson]:
        """Return all stored lessons in insertion order."""
        return list(self._lessons)

    def clear(self) -> None:
        """Remove all stored failures and lessons."""
        self._failures.clear()
        self._lessons.clear()
