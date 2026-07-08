"""Tests for the in-memory store."""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    Lesson,
    MemoryStore,
    Task,
    VerificationResult,
)


def _trace(instruction: str, reason: str = "output is empty") -> FailureTrace:
    return FailureTrace(
        task=Task(instruction=instruction),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason=reason, rule_name="non_empty_output"
        ),
        attempt=1,
    )


def test_add_and_read_failures() -> None:
    store = MemoryStore()
    store.add_failure(_trace("a"))
    store.add_failure(_trace("b"))
    assert len(store.failures()) == 2


def test_recent_failures_returns_newest_within_limit() -> None:
    store = MemoryStore()
    for i in range(4):
        store.add_failure(_trace(f"task-{i}"))
    recent = store.recent_failures(limit=2)
    assert [t.task.instruction for t in recent] == ["task-2", "task-3"]


def test_relevant_lessons_matches_on_keywords() -> None:
    store = MemoryStore()
    store.add_lesson(
        Lesson(
            summary="On task 'summarize the release notes', it failed.",
            avoid_next_time="x",
            recommended_prompt_patch="y",
            tags=["empty-output"],
        )
    )
    store.add_lesson(
        Lesson(
            summary="On task 'translate the invoice', it failed.",
            avoid_next_time="x",
            recommended_prompt_patch="y",
            tags=["missing-terms"],
        )
    )
    matched = store.relevant_lessons(Task(instruction="summarize the release notes"))
    assert len(matched) == 1
    assert "release notes" in matched[0].summary


def test_relevant_lessons_falls_back_to_recent_when_no_overlap() -> None:
    store = MemoryStore()
    store.add_lesson(
        Lesson(
            summary="unrelated topic entirely",
            avoid_next_time="x",
            recommended_prompt_patch="y",
            tags=["general"],
        )
    )
    matched = store.relevant_lessons(Task(instruction="completely different words"))
    assert len(matched) == 1


def test_relevant_lessons_empty_when_no_lessons() -> None:
    store = MemoryStore()
    assert store.relevant_lessons(Task(instruction="anything")) == []


def test_failures_returns_a_copy() -> None:
    store = MemoryStore()
    store.add_failure(_trace("a"))
    snapshot = store.failures()
    snapshot.clear()
    assert len(store.failures()) == 1


def test_clear_empties_the_store() -> None:
    store = MemoryStore()
    store.add_failure(_trace("a"))
    store.add_lesson(
        Lesson(summary="s", avoid_next_time="a", recommended_prompt_patch="p")
    )
    store.clear()
    assert store.failures() == []
    assert store.lessons() == []
