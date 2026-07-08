"""Tests for the evaluation summary builder."""

from __future__ import annotations

from entropy_loop_core import (
    EntropyLoop,
    MemoryStore,
    RetryContext,
    Task,
    Verifier,
    generate_regression_case,
    summarize,
)


def _agent_fails_once(task: Task, ctx: RetryContext) -> object:
    if not ctx.lessons:
        return "missing the term"
    return "status: ok"


def test_summary_of_successful_run_with_one_failure() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(
        verifier=Verifier().require_non_empty().require_terms(["status"]),
        memory=memory,
        max_attempts=3,
    )
    result = loop.run(Task(id="t", instruction="report status"), _agent_fails_once)
    cases = [generate_regression_case(trace) for trace in result.failures]

    summary = summarize(result, cases)

    assert summary.success is True
    assert summary.final_status == "success"
    assert summary.total_attempts == 2
    assert summary.failure_count == 1
    assert summary.categories == {"missing_required_term": 1}
    assert summary.generated_regression_cases == 1


def test_summary_of_failed_run_counts_categories() -> None:
    memory = MemoryStore()
    loop = EntropyLoop(
        verifier=Verifier().require_non_empty(), memory=memory, max_attempts=2
    )
    result = loop.run(Task(id="t", instruction="x"), lambda task, ctx: "")

    summary = summarize(result)

    assert summary.success is False
    assert summary.failure_count == 2
    assert summary.categories == {"empty_output": 2}
    assert summary.generated_regression_cases == 0
