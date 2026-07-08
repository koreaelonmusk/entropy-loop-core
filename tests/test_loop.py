"""Tests for the entropy loop."""

from __future__ import annotations

import pytest

from entropy_loop_core import (
    EntropyLoop,
    LoopStatus,
    MemoryStore,
    Task,
    Verifier,
)


def _fail_once_agent(task: Task, attempt: int) -> str:
    """Fail on the first attempt, then succeed."""
    if attempt == 1:
        return ""
    return f"done: {task.prompt}"


def test_succeeds_after_one_failure() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=3)

    result = loop.run(Task(prompt="do the thing"), _fail_once_agent)

    assert result.status is LoopStatus.SUCCESS
    assert result.attempts == 2
    assert result.output == "done: do the thing"
    assert result.errors == ["output is empty"]
    assert len(memory.failures()) == 1


def test_succeeds_on_first_attempt() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory)

    result = loop.run(Task(prompt="x"), lambda task, attempt: "answer")

    assert result.status is LoopStatus.SUCCESS
    assert result.attempts == 1
    assert memory.failures() == []


def test_gives_up_after_max_attempts() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=2)

    result = loop.run(Task(prompt="never works"), lambda task, attempt: "")

    assert result.status is LoopStatus.FAILED
    assert result.attempts == 2
    assert result.output is None
    assert len(result.errors) == 2
    assert len(memory.failures()) == 2


def test_agent_exception_is_recorded_as_failure() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=1)

    def boom(task: Task, attempt: int) -> str:
        raise RuntimeError("kaboom")

    result = loop.run(Task(prompt="x"), boom)

    assert result.status is LoopStatus.FAILED
    assert "agent raised RuntimeError: kaboom" in result.errors[0]


def test_invalid_max_attempts_raises() -> None:
    with pytest.raises(ValueError):
        EntropyLoop(verifier=Verifier(), memory=MemoryStore(), max_attempts=0)
