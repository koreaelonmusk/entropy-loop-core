"""Tests for the failure-compiling entropy loop."""

from __future__ import annotations

import pytest

from entropy_loop_core import (
    AgentOutput,
    EntropyLoop,
    MemoryStore,
    RetryContext,
    Task,
    Verifier,
)


def _learns_from_lessons(task: Task, context: RetryContext) -> AgentOutput:
    """Omit the required term until a lesson has been fed back."""
    if not context.lessons:
        return AgentOutput(content="finished")
    return AgentOutput(content="status: finished")


def _verifier() -> Verifier:
    return Verifier().require_non_empty().require_terms(["status"])


def test_compiles_failure_then_succeeds_on_retry() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(verifier=_verifier(), memory=memory, max_attempts=3)

    result = loop.run(Task(id="t", instruction="report status"), _learns_from_lessons)

    assert result.status == "success"
    assert result.attempts == 2
    assert result.output is not None
    assert "status" in result.output.content

    # One failure was traced, compiled into a lesson, and remembered.
    assert len(result.failures) == 1
    assert len(result.lessons) == 1
    assert result.errors and "status" in result.errors[0]
    assert len(memory.recent_failures()) == 1
    assert len(memory.all_lessons()) == 1


def test_succeeds_on_first_attempt_without_artifacts() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier().require_non_empty(), memory=memory)

    result = loop.run(
        Task(id="t", instruction="x"),
        lambda task, ctx: AgentOutput(content="answer"),
    )

    assert result.status == "success"
    assert result.attempts == 1
    assert result.failures == []
    assert result.errors == []


def test_accepts_plain_string_output() -> None:
    loop = EntropyLoop(verifier=Verifier().require_non_empty(), memory=MemoryStore())
    result = loop.run(Task(id="t", instruction="x"), lambda task, ctx: "plain answer")
    assert result.status == "success"
    assert result.output is not None
    assert result.output.content == "plain answer"


def test_retry_context_carries_prior_failures() -> None:
    seen: list[int] = []

    def agent(task: Task, ctx: RetryContext) -> AgentOutput:
        seen.append(len(ctx.prior_failures))
        return AgentOutput(content="")  # always fails non-empty

    loop = EntropyLoop(
        verifier=Verifier().require_non_empty(), memory=MemoryStore(), max_attempts=3
    )
    loop.run(Task(id="t", instruction="x"), agent)
    assert seen == [0, 1, 2]


def test_gives_up_after_max_attempts() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(
        verifier=Verifier().require_non_empty(), memory=memory, max_attempts=2
    )

    result = loop.run(
        Task(id="t", instruction="never"), lambda task, ctx: AgentOutput(content="")
    )

    assert result.status == "failed"
    assert result.attempts == 2
    assert result.output is None
    assert len(result.failures) == 2
    assert len(result.errors) == 2


def test_agent_exception_is_traced_as_critical_failure() -> None:
    loop = EntropyLoop(
        verifier=Verifier().require_non_empty(), memory=MemoryStore(), max_attempts=1
    )

    def boom(task: Task, ctx: RetryContext) -> AgentOutput:
        raise RuntimeError("kaboom")

    result = loop.run(Task(id="t", instruction="x"), boom)

    assert result.status == "failed"
    trace = result.failures[0]
    assert trace.verification_result.rule_name == "agent_exception"
    assert trace.verification_result.severity == "critical"
    assert "RuntimeError: kaboom" in trace.verification_result.reason


def test_invalid_max_attempts_raises() -> None:
    with pytest.raises(ValueError):
        EntropyLoop(verifier=Verifier(), memory=MemoryStore(), max_attempts=0)
