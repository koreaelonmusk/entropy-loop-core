"""Tests for the in-memory store."""

from __future__ import annotations

from entropy_loop_core import Failure, Lesson, MemoryStore


def test_record_and_read_failures() -> None:
    store = MemoryStore()
    store.record_failure(Failure(task_prompt="a", attempt=1, reason="boom"))
    store.record_failure(Failure(task_prompt="b", attempt=1, reason="nope"))

    failures = store.failures()
    assert len(failures) == 2
    assert failures[0].reason == "boom"


def test_failures_for_filters_by_prompt() -> None:
    store = MemoryStore()
    store.record_failure(Failure(task_prompt="a", attempt=1, reason="x"))
    store.record_failure(Failure(task_prompt="a", attempt=2, reason="y"))
    store.record_failure(Failure(task_prompt="b", attempt=1, reason="z"))

    matched = store.failures_for("a")
    assert [f.attempt for f in matched] == [1, 2]


def test_record_and_read_lessons() -> None:
    store = MemoryStore()
    store.record_lesson(Lesson(topic="retry", insight="add more context"))
    assert store.lessons()[0].insight == "add more context"


def test_clear_empties_the_store() -> None:
    store = MemoryStore()
    store.record_failure(Failure(task_prompt="a", attempt=1, reason="x"))
    store.record_lesson(Lesson(topic="t", insight="i"))
    store.clear()
    assert store.failures() == []
    assert store.lessons() == []


def test_failures_returns_a_copy() -> None:
    store = MemoryStore()
    store.record_failure(Failure(task_prompt="a", attempt=1, reason="x"))
    snapshot = store.failures()
    snapshot.clear()
    assert len(store.failures()) == 1
