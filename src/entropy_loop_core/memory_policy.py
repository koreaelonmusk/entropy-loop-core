"""Deterministic memory policy and lesson compaction.

Where earlier versions generated lessons and replayed regression cases, this
module decides **what failure memory to keep**. :class:`LessonCompactor` applies
a :class:`~entropy_loop_core.types.MemoryPolicy` to a list of lessons: it drops
empty and low-signal lessons, deduplicates by a guidance fingerprint or by
failure category, and caps how many lessons are retained.

Everything here is deterministic and pure Python — **no LLM calls, no network,
no database, no hidden persistence, and no vector store**. The compaction summary
is a fixed template, not a model-written sentence.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .types import (
    CompactionResult,
    Lesson,
    LessonMemory,
    MemoryPolicy,
    RegressionCase,
)

# The public-safe failure categories a lesson may be tagged with.
_KNOWN_CATEGORIES = frozenset(
    {
        "empty_output",
        "missing_required_term",
        "invalid_json",
        "too_long",
        "agent_exception",
        "unknown",
    }
)


def _is_empty(lesson: Lesson) -> bool:
    """Return True when a lesson carries no usable content."""
    return not (
        lesson.summary.strip()
        or lesson.avoid_next_time.strip()
        or lesson.recommended_prompt_patch.strip()
    )


def _fingerprint(lesson: Lesson) -> str:
    """A deterministic fingerprint of a lesson's guidance.

    Built from the avoidance guidance, the prompt patch, and the sorted tags —
    deliberately **not** the summary, which varies per occurrence (attempt
    number, exact reason). Lessons giving the same guidance share a fingerprint.
    """
    basis = "|".join(
        [lesson.avoid_next_time, lesson.recommended_prompt_patch, *sorted(lesson.tags)]
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def _category_of(lesson: Lesson) -> str:
    """Return the failure category tag of a lesson, or ``"unknown"``."""
    for tag in lesson.tags:
        if tag in _KNOWN_CATEGORIES:
            return tag
    return "unknown"


def _dedupe(
    lessons: list[Lesson], key: Callable[[Lesson], str], keep_latest: bool
) -> tuple[list[Lesson], int]:
    """Deduplicate lessons by ``key``, keeping newest or oldest per key.

    Output preserves the relative order of the kept lessons. Deterministic.
    """
    chosen: dict[str, tuple[int, Lesson]] = {}
    for index, lesson in enumerate(lessons):
        k = key(lesson)
        if keep_latest or k not in chosen:
            chosen[k] = (index, lesson)
    kept = [lesson for _, lesson in sorted(chosen.values(), key=lambda pair: pair[0])]
    return kept, len(lessons) - len(kept)


class LessonCompactor:
    """Applies a :class:`MemoryPolicy` to lessons, deterministically.

    Use :meth:`compact` for a list of lessons or :meth:`compact_memory` for a
    :class:`LessonMemory`. The compactor never calls a model or the network and
    always produces the same output for the same input and policy.
    """

    def compact(
        self,
        lessons: list[Lesson],
        policy: MemoryPolicy | None = None,
        regression_cases: Sequence[RegressionCase] = (),
    ) -> CompactionResult:
        """Compact ``lessons`` according to ``policy``.

        Args:
            lessons: The lessons to compact, in chronological order (newest last).
            policy: The policy to apply; a default :class:`MemoryPolicy` if None.
            regression_cases: Optional cases used only when
                ``policy.prefer_regression_cases`` is set, to prefer keeping
                lessons whose category has a regression case.

        Returns:
            A :class:`CompactionResult` with the kept lessons and counts.
        """
        policy = policy or MemoryPolicy()
        input_count = len(lessons)
        dropped: Counter[str] = Counter()
        merged_count = 0
        working = list(lessons)

        if policy.drop_empty_lessons:
            kept = [lesson for lesson in working if not _is_empty(lesson)]
            dropped["empty"] += len(working) - len(kept)
            working = kept

        if policy.min_occurrences > 1:
            counts = Counter(_fingerprint(lesson) for lesson in working)
            kept = [
                lesson
                for lesson in working
                if counts[_fingerprint(lesson)] >= policy.min_occurrences
            ]
            dropped["below_min_occurrences"] += len(working) - len(kept)
            working = kept

        if policy.dedupe_by_fingerprint:
            working, merged = _dedupe(working, _fingerprint, policy.keep_latest)
            merged_count += merged
            dropped["duplicate_fingerprint"] += merged

        if policy.dedupe_by_failure_category:
            working, merged = _dedupe(working, _category_of, policy.keep_latest)
            merged_count += merged
            dropped["duplicate_category"] += merged

        if policy.max_lessons_per_category is not None:
            working, count = self._cap_per_category(
                working, policy.max_lessons_per_category, policy.keep_latest
            )
            dropped["per_category_limit"] += count

        if policy.max_lessons is not None and len(working) > policy.max_lessons:
            preferred = (
                {case.category for case in regression_cases}
                if policy.prefer_regression_cases
                else set()
            )
            working, count = self._cap_total(
                working, policy.max_lessons, policy.keep_latest, preferred
            )
            dropped["max_lessons_limit"] += count

        output_count = len(working)
        summary = (
            f"Compacted {input_count} lesson(s) to {output_count}; "
            f"dropped {input_count - output_count} ({merged_count} duplicate(s))."
        )
        return CompactionResult(
            input_count=input_count,
            output_count=output_count,
            dropped_count=input_count - output_count,
            merged_count=merged_count,
            lessons=working,
            summary=summary,
            dropped_reasons=dict(dropped),
            category_counts=dict(Counter(_category_of(lesson) for lesson in working)),
        )

    def compact_memory(
        self,
        memory: LessonMemory,
        policy: MemoryPolicy | None = None,
        regression_cases: Sequence[RegressionCase] = (),
    ) -> LessonMemory:
        """Compact the lessons inside a :class:`LessonMemory`.

        Returns a new :class:`LessonMemory` with the compacted lessons; the
        compaction summary is recorded under ``metadata["compaction_summary"]``.
        """
        result = self.compact(memory.lessons, policy, regression_cases)
        return LessonMemory(
            lessons=result.lessons,
            metadata={**memory.metadata, "compaction_summary": result.summary},
            source_trace_count=memory.source_trace_count,
            compacted_at=memory.compacted_at,
            policy_name=memory.policy_name,
        )

    def _cap_per_category(
        self, lessons: list[Lesson], limit: int, keep_latest: bool
    ) -> tuple[list[Lesson], int]:
        """Keep at most ``limit`` lessons per category, preserving order."""
        by_category: dict[str, list[int]] = {}
        for index, lesson in enumerate(lessons):
            by_category.setdefault(_category_of(lesson), []).append(index)
        keep: set[int] = set()
        for indices in by_category.values():
            chosen = indices[-limit:] if keep_latest else indices[:limit]
            keep.update(chosen)
        kept = [lesson for index, lesson in enumerate(lessons) if index in keep]
        return kept, len(lessons) - len(kept)

    def _cap_total(
        self,
        lessons: list[Lesson],
        limit: int,
        keep_latest: bool,
        preferred_categories: set[str],
    ) -> tuple[list[Lesson], int]:
        """Keep ``limit`` lessons, preferring preferred categories then recency."""
        indexed = list(enumerate(lessons))

        def rank(item: tuple[int, Lesson]) -> tuple[int, int]:
            index, lesson = item
            pref = 1 if _category_of(lesson) in preferred_categories else 0
            recency = index if keep_latest else -index
            return (pref, recency)

        top = sorted(indexed, key=rank, reverse=True)[:limit]
        kept = [lesson for _, lesson in sorted(top, key=lambda pair: pair[0])]
        return kept, len(lessons) - limit


def export_memory_policy(policy: MemoryPolicy) -> dict[str, Any]:
    """Render a memory policy as a plain, JSON-compatible dictionary."""
    return policy.model_dump()


def import_memory_policy(data: dict[str, Any]) -> MemoryPolicy:
    """Build a memory policy from a plain dictionary."""
    return MemoryPolicy.model_validate(data)


def export_lesson_memory(memory: LessonMemory) -> dict[str, Any]:
    """Render lesson memory as a plain, JSON-compatible dictionary."""
    return memory.model_dump()


def import_lesson_memory(data: dict[str, Any]) -> LessonMemory:
    """Build lesson memory from a plain dictionary."""
    return LessonMemory.model_validate(data)


def export_compaction_result(result: CompactionResult) -> dict[str, Any]:
    """Render a compaction result as a plain, JSON-compatible dictionary."""
    return result.model_dump()


def save_lesson_memory(memory: LessonMemory, path: str | Path) -> None:
    """Write lesson memory to a local JSON file.

    Args:
        memory: The memory to save.
        path: Destination path on the local filesystem.
    """
    Path(path).write_text(
        json.dumps(export_lesson_memory(memory), indent=2), encoding="utf-8"
    )


def load_lesson_memory(path: str | Path) -> LessonMemory:
    """Read lesson memory from a local JSON file."""
    return import_lesson_memory(json.loads(Path(path).read_text(encoding="utf-8")))
