"""Tests for the typed data contract."""

from __future__ import annotations

from datetime import datetime

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    Lesson,
    LoopResult,
    RegressionCase,
    RetryContext,
    Task,
    VerificationResult,
)


def test_task_defaults() -> None:
    task = Task(id="t1", instruction="do it")
    assert task.metadata == {}


def test_agent_output_metadata_accepts_any() -> None:
    out = AgentOutput(content="hi", metadata={"tokens": 3})
    assert out.metadata["tokens"] == 3


def test_verification_result_defaults() -> None:
    result = VerificationResult(passed=True)
    assert result.reason == ""
    assert result.severity == "error"


def test_failure_trace_has_timestamp() -> None:
    trace = FailureTrace(
        task=Task(id="t1", instruction="x"),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason="output is empty", rule_name="non_empty_output"
        ),
        attempt=1,
    )
    assert isinstance(trace.timestamp, datetime)
    assert trace.attempt == 1


def test_retry_context_defaults_empty() -> None:
    ctx = RetryContext(attempt=1)
    assert ctx.prior_failures == []
    assert ctx.lessons == []


def test_loop_result_and_lesson_and_regression_construct() -> None:
    result = LoopResult(status="success", attempts=1, output=AgentOutput(content="ok"))
    assert result.errors == []

    lesson = Lesson(summary="s", avoid_next_time="a", recommended_prompt_patch="p")
    assert lesson.tags == []

    case = RegressionCase(
        name="regression_x_non_empty_output",
        instruction="x",
        expected_rule="non_empty_output",
        failure_reason="output is empty",
    )
    assert case.expected_rule == "non_empty_output"
