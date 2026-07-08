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
        task=Task(id="t", instruction=instruction),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason=reason, rule_name="non_empty_output"
        ),
        attempt=1,
    )


def _lesson(summary: str, tags: list[str]) -> Lesson:
    return Lesson(
        summary=summary,
        avoid_next_time="x",
        recommended_prompt_patch="y",
        tags=tags,
    )


def test_recent_failures_returns_newest_within_limit() -> None:
    store = MemoryStore()
    for i in range(4):
        store.add_failure(_trace(f"task-{i}"))
    recent = store.recent_failures(limit=2)
    assert [t.task.instruction for t in recent] == ["task-2", "task-3"]


def test_all_lessons_returns_a_copy() -> None:
    store = MemoryStore()
    store.add_lesson(_lesson("a lesson", ["empty-output"]))
    snapshot = store.all_lessons()
    snapshot.clear()
    assert len(store.all_lessons()) == 1


def test_relevant_lessons_matches_on_keywords() -> None:
    store = MemoryStore()
    store.add_lesson(_lesson("On task 'summarize the release notes', failed.", ["a"]))
    store.add_lesson(_lesson("On task 'translate the invoice', failed.", ["b"]))
    task = Task(id="t", instruction="summarize release notes")
    matched = store.relevant_lessons(task)
    assert len(matched) == 1
    assert "release notes" in matched[0].summary


def test_relevant_lessons_falls_back_to_recent_when_no_overlap() -> None:
    store = MemoryStore()
    store.add_lesson(_lesson("unrelated topic entirely", ["general"]))
    matched = store.relevant_lessons(Task(id="t", instruction="different words here"))
    assert len(matched) == 1


def test_relevant_lessons_empty_when_no_lessons() -> None:
    store = MemoryStore()
    assert store.relevant_lessons(Task(id="t", instruction="anything")) == []


def test_clear_empties_the_store() -> None:
    store = MemoryStore()
    store.add_failure(_trace("a"))
    store.add_lesson(_lesson("s", ["t"]))
    store.clear()
    assert store.recent_failures() == []
    assert store.all_lessons() == []
