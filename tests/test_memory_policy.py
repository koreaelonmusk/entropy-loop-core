"""Tests for the memory policy and lesson compaction."""

from __future__ import annotations

import pytest

from entropy_loop_core import (
    CompactionResult,
    Lesson,
    LessonCompactor,
    LessonMemory,
    MemoryPolicy,
    export_lesson_memory,
    export_memory_policy,
    import_lesson_memory,
    import_memory_policy,
    load_lesson_memory,
    save_lesson_memory,
)


def _lesson(category: str, patch: str = "do X", rule: str = "some_rule") -> Lesson:
    return Lesson(
        summary=f"failed with {category}",
        avoid_next_time=f"avoid {category}",
        recommended_prompt_patch=patch,
        tags=[category, rule],
    )


# --- MemoryPolicy ---------------------------------------------------------


def test_default_policy() -> None:
    policy = MemoryPolicy()
    assert policy.dedupe_by_fingerprint is True
    assert policy.max_lessons is None
    assert policy.min_occurrences == 1


def test_policy_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        MemoryPolicy(max_lessons=-1)
    with pytest.raises(ValueError):
        MemoryPolicy(min_occurrences=0)
    with pytest.raises(ValueError):
        MemoryPolicy(max_lessons_per_category=-3)


# --- LessonCompactor ------------------------------------------------------


def test_compact_empty_list() -> None:
    result = LessonCompactor().compact([])
    assert isinstance(result, CompactionResult)
    assert result.input_count == 0
    assert result.output_count == 0
    assert result.lessons == []


def test_compact_keeps_unique_lessons() -> None:
    lessons = [_lesson("empty_output"), _lesson("invalid_json")]
    result = LessonCompactor().compact(lessons, MemoryPolicy())
    assert result.output_count == 2
    assert result.merged_count == 0


def test_compact_drops_fingerprint_duplicates() -> None:
    # Three lessons with identical guidance/tags collapse to one.
    lessons = [_lesson("missing_required_term") for _ in range(3)]
    result = LessonCompactor().compact(
        lessons, MemoryPolicy(dedupe_by_fingerprint=True)
    )
    assert result.output_count == 1
    assert result.merged_count == 2
    assert result.dropped_reasons["duplicate_fingerprint"] == 2


def test_compact_respects_max_lessons() -> None:
    lessons = [_lesson("empty_output", patch=f"p{i}") for i in range(5)]
    result = LessonCompactor().compact(
        lessons, MemoryPolicy(dedupe_by_fingerprint=False, max_lessons=2)
    )
    assert result.output_count == 2


def test_keep_latest_selects_newest() -> None:
    lessons = [_lesson("empty_output", patch=f"p{i}") for i in range(3)]
    # dedupe by category keeps one; keep_latest -> the last one (p2).
    result = LessonCompactor().compact(
        lessons,
        MemoryPolicy(
            dedupe_by_fingerprint=False,
            dedupe_by_failure_category=True,
            keep_latest=True,
        ),
    )
    assert result.output_count == 1
    assert result.lessons[0].recommended_prompt_patch == "p2"

    oldest = LessonCompactor().compact(
        lessons,
        MemoryPolicy(
            dedupe_by_fingerprint=False,
            dedupe_by_failure_category=True,
            keep_latest=False,
        ),
    )
    assert oldest.lessons[0].recommended_prompt_patch == "p0"


def test_drop_empty_lessons() -> None:
    empty = Lesson(summary="", avoid_next_time="", recommended_prompt_patch="")
    lessons = [_lesson("empty_output"), empty]
    result = LessonCompactor().compact(lessons, MemoryPolicy(drop_empty_lessons=True))
    assert result.output_count == 1
    assert result.dropped_reasons["empty"] == 1


def test_min_occurrences_drops_rare() -> None:
    lessons = [
        _lesson("empty_output"),
        _lesson("empty_output"),
        _lesson("invalid_json"),  # appears once
    ]
    result = LessonCompactor().compact(
        lessons,
        MemoryPolicy(dedupe_by_fingerprint=False, min_occurrences=2),
    )
    # invalid_json (1 occurrence) is dropped; the two empty_output remain.
    assert all("invalid_json" not in lesson.tags for lesson in result.lessons)
    assert result.dropped_reasons["below_min_occurrences"] == 1


def test_compaction_is_deterministic() -> None:
    lessons = [_lesson("empty_output"), _lesson("empty_output"), _lesson("too_long")]
    compactor = LessonCompactor()
    first = compactor.compact(lessons, MemoryPolicy())
    second = compactor.compact(lessons, MemoryPolicy())
    assert first == second
    assert "Compacted 3 lesson(s) to 2" in first.summary


def test_compact_memory_records_summary() -> None:
    memory = LessonMemory(lessons=[_lesson("empty_output"), _lesson("empty_output")])
    out = LessonCompactor().compact_memory(memory, MemoryPolicy())
    assert isinstance(out, LessonMemory)
    assert len(out.lessons) == 1
    assert "compaction_summary" in out.metadata


# --- serialization --------------------------------------------------------


def test_memory_policy_roundtrip() -> None:
    policy = MemoryPolicy(max_lessons=5, dedupe_by_failure_category=True)
    assert import_memory_policy(export_memory_policy(policy)) == policy


def test_lesson_memory_roundtrip() -> None:
    memory = LessonMemory(lessons=[_lesson("empty_output")], source_trace_count=3)
    assert import_lesson_memory(export_lesson_memory(memory)) == memory


def test_save_and_load_lesson_memory(tmp_path) -> None:
    memory = LessonMemory(lessons=[_lesson("invalid_json")])
    path = tmp_path / "memory.json"
    save_lesson_memory(memory, path)
    assert path.exists()
    assert load_lesson_memory(path) == memory
