"""Tests for the typed data contract."""

from __future__ import annotations

from datetime import datetime

from entropy_loop_core import (
    AgentOutput,
    EvaluationSummary,
    FailureTrace,
    Lesson,
    LoopResult,
    RegressionCase,
    RetryContext,
    Task,
    VerificationResult,
)


def _trace(instruction: str = "x", category: str = "empty_output") -> FailureTrace:
    return FailureTrace(
        task=Task(id="t1", instruction=instruction),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False,
            reason="output is empty",
            rule_name="non_empty_output",
            category=category,
        ),
        attempt=1,
    )


def test_task_and_output_defaults() -> None:
    assert Task(id="t1", instruction="do it").metadata == {}
    assert AgentOutput(content="hi", metadata={"tokens": 3}).metadata["tokens"] == 3


def test_verification_result_defaults() -> None:
    result = VerificationResult(passed=True)
    assert result.reason == ""
    assert result.severity == "error"
    assert result.category == "unknown"
    assert result.details == {}


def test_failure_trace_category_comes_from_result() -> None:
    trace = _trace(category="missing_required_term")
    assert trace.category == "missing_required_term"
    assert isinstance(trace.timestamp, datetime)


def test_failure_trace_fingerprint_is_deterministic() -> None:
    assert _trace().fingerprint == _trace().fingerprint


def test_failure_trace_fingerprint_varies_with_instruction() -> None:
    assert _trace("summarize notes").fingerprint != _trace("translate text").fingerprint


def test_retry_context_defaults_empty() -> None:
    ctx = RetryContext(attempt=1)
    assert ctx.prior_failures == []
    assert ctx.lessons == []


def test_loop_result_lesson_regression_and_summary_construct() -> None:
    result = LoopResult(status="success", attempts=1, output=AgentOutput(content="ok"))
    assert result.errors == []

    lesson = Lesson(summary="s", avoid_next_time="a", recommended_prompt_patch="p")
    assert lesson.tags == []

    case = RegressionCase(
        name="regression_x_non_empty_output",
        instruction="x",
        expected_rule="non_empty_output",
        failure_reason="output is empty",
        category="empty_output",
    )
    assert case.category == "empty_output"

    summary = EvaluationSummary(
        total_attempts=2, success=True, failure_count=1, final_status="success"
    )
    assert summary.categories == {}
    assert summary.generated_regression_cases == 0
