"""Tests for regression-case generation and export."""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    Task,
    VerificationResult,
    export_regression_case,
    export_regression_cases,
    generate_regression_case,
)


def _trace() -> FailureTrace:
    return FailureTrace(
        task=Task(id="t1", instruction="Summarize the Release Notes!"),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False,
            reason="output is empty",
            rule_name="non_empty_output",
            category="empty_output",
        ),
        attempt=1,
    )


def test_regression_case_fields_and_category() -> None:
    case = generate_regression_case(_trace())
    assert case.instruction == "Summarize the Release Notes!"
    assert case.expected_rule == "non_empty_output"
    assert case.failure_reason == "output is empty"
    assert case.category == "empty_output"


def test_regression_name_is_identifier_friendly_and_stable() -> None:
    name = generate_regression_case(_trace()).name
    assert name == generate_regression_case(_trace()).name
    assert " " not in name
    assert name.startswith("regression_")
    assert "non_empty_output" in name


def test_export_regression_case_is_a_plain_dict() -> None:
    case = generate_regression_case(_trace())
    exported = export_regression_case(case)
    assert isinstance(exported, dict)
    assert exported["expected_rule"] == "non_empty_output"
    assert exported["category"] == "empty_output"


def test_export_regression_cases_preserves_order() -> None:
    cases = [generate_regression_case(_trace())]
    exported = export_regression_cases(cases)
    assert isinstance(exported, list)
    assert exported[0]["name"] == cases[0].name
