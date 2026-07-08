"""Tests for regression-case generation."""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    Task,
    VerificationResult,
    generate_regression_case,
)


def _trace() -> FailureTrace:
    return FailureTrace(
        task=Task(id="t1", instruction="Summarize the Release Notes!"),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason="output is empty", rule_name="non_empty_output"
        ),
        attempt=1,
    )


def test_regression_case_fields() -> None:
    case = generate_regression_case(_trace())
    assert case.instruction == "Summarize the Release Notes!"
    assert case.expected_rule == "non_empty_output"
    assert case.failure_reason == "output is empty"


def test_regression_name_is_identifier_friendly_and_stable() -> None:
    name = generate_regression_case(_trace()).name
    assert name == generate_regression_case(_trace()).name  # deterministic
    assert " " not in name
    assert name.startswith("regression_")
    assert "non_empty_output" in name
