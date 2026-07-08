"""Tests for the failure-compiling entropy loop."""

from __future__ import annotations

import pytest

from entropy_loop_core import (
    AgentContext,
    AgentOutput,
    EntropyLoop,
    LoopStatus,
    MemoryStore,
    Task,
    Verifier,
)


def _learns_from_lessons(context: AgentContext) -> AgentOutput:
    """Fail with empty output until a lesson has been compiled and fed back."""
    if not context.lessons:
        return AgentOutput(content="")
    return AgentOutput(content=f"done: {context.task.instruction}")


def _new_loop(**kwargs: object) -> tuple[EntropyLoop, MemoryStore]:
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, **kwargs)
    return loop, memory


def test_compiles_failure_then_succeeds_on_retry() -> None:
    loop, memory = _new_loop(max_attempts=3)

    result = loop.run(Task(instruction="do the thing"), _learns_from_lessons)

    assert result.status is LoopStatus.SUCCESS
    assert result.attempts == 2
    assert result.output is not None
    assert result.output.content == "done: do the thing"

    # One failure was traced, compiled into a lesson, and turned into a case.
    assert len(result.failures) == 1
    assert len(result.lessons) == 1
    assert len(result.regression_cases) == 1
    assert result.regression_cases[0].expected_rule == "non_empty_output"

    # And all of it was remembered.
    assert len(memory.failures()) == 1
    assert len(memory.lessons()) == 1


def test_succeeds_on_first_attempt_without_artifacts() -> None:
    loop, memory = _new_loop()

    result = loop.run(Task(instruction="x"), lambda ctx: AgentOutput(content="answer"))

    assert result.status is LoopStatus.SUCCESS
    assert result.attempts == 1
    assert result.failures == []
    assert result.lessons == []
    assert memory.failures() == []


def test_accepts_plain_string_output() -> None:
    loop, _ = _new_loop()
    result = loop.run(Task(instruction="x"), lambda ctx: "plain answer")
    assert result.status is LoopStatus.SUCCESS
    assert result.output is not None
    assert result.output.content == "plain answer"


def test_gives_up_after_max_attempts() -> None:
    loop, memory = _new_loop(max_attempts=2)

    result = loop.run(
        Task(instruction="never works"), lambda ctx: AgentOutput(content="")
    )

    assert result.status is LoopStatus.FAILED
    assert result.attempts == 2
    assert result.output is None
    assert len(result.failures) == 2
    assert len(memory.failures()) == 2


def test_agent_exception_is_traced_as_critical_failure() -> None:
    loop, _ = _new_loop(max_attempts=1)

    def boom(context: AgentContext) -> AgentOutput:
        raise RuntimeError("kaboom")

    result = loop.run(Task(instruction="x"), boom)

    assert result.status is LoopStatus.FAILED
    trace = result.failures[0]
    assert trace.verification_result.rule_name == "agent_exception"
    assert "RuntimeError: kaboom" in trace.verification_result.reason


def test_regression_generation_can_be_disabled() -> None:
    loop, _ = _new_loop(max_attempts=1, generate_regressions=False)
    result = loop.run(Task(instruction="x"), lambda ctx: AgentOutput(content=""))
    assert result.regression_cases == []
    assert len(result.lessons) == 1


def test_invalid_max_attempts_raises() -> None:
    with pytest.raises(ValueError):
        EntropyLoop(verifier=Verifier(), memory=MemoryStore(), max_attempts=0)
