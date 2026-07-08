"""Tests for the regression replay engine."""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    RegressionCase,
    RegressionRunner,
    RegressionSuite,
    RetryContext,
    Task,
    Verifier,
    export_regression_suite,
    import_regression_suite,
    load_regression_suite,
    save_regression_suite,
)


def _case(name: str = "case-1") -> RegressionCase:
    return RegressionCase(
        name=name,
        instruction="report the job status",
        expected_rule="contains_required_terms",
        failure_reason="missing required terms: ['status']",
        category="missing_required_term",
    )


def _verifier() -> Verifier:
    return Verifier().require_non_empty().require_terms(["status"])


def _good_agent(task: Task, ctx: RetryContext) -> AgentOutput:
    return AgentOutput(content="status: ok")


def _bad_agent(task: Task, ctx: RetryContext) -> AgentOutput:
    return AgentOutput(content="still no keyword")


def test_suite_creation() -> None:
    suite = RegressionSuite(name="s", cases=[_case()])
    assert suite.name == "s"
    assert len(suite.cases) == 1
    assert suite.metadata == {}


def test_run_case_passes_when_output_is_fixed() -> None:
    result = RegressionRunner().run_case(_case(), _good_agent, _verifier())
    assert result.passed is True
    assert result.output is not None
    assert result.verification_result is not None
    assert result.verification_result.passed is True
    assert result.error is None


def test_run_case_fails_when_bug_remains() -> None:
    result = RegressionRunner().run_case(_case(), _bad_agent, _verifier())
    assert result.passed is False
    assert result.verification_result is not None
    assert result.verification_result.category == "missing_required_term"


def test_run_case_handles_agent_exception() -> None:
    def boom(task: Task, ctx: RetryContext) -> AgentOutput:
        raise RuntimeError("kaboom")

    result = RegressionRunner().run_case(_case(), boom, _verifier())
    assert result.passed is False
    assert result.output is None
    assert "RuntimeError: kaboom" in result.error


def test_run_suite_summary_and_success_rate() -> None:
    suite = RegressionSuite(
        name="mixed",
        cases=[_case("a"), _case("b")],
    )

    # First case passes (good agent), so run each with a different agent by
    # replaying two single-case suites and combining is overkill; instead use a
    # suite where the agent fixes everything.
    report = RegressionRunner().run_suite(suite, _good_agent, _verifier())
    assert report.total_cases == 2
    assert report.passed == 2
    assert report.failed == 0
    assert report.success_rate == 100.0

    failed_report = RegressionRunner().run_suite(suite, _bad_agent, _verifier())
    assert failed_report.passed == 0
    assert failed_report.failed == 2
    assert failed_report.success_rate == 0.0


def test_empty_suite_success_rate_is_zero() -> None:
    report = RegressionRunner().run_suite(
        RegressionSuite(name="empty"), _good_agent, _verifier()
    )
    assert report.total_cases == 0
    assert report.success_rate == 0.0


def test_export_import_roundtrip() -> None:
    suite = RegressionSuite(name="s", cases=[_case()], metadata={"origin": "test"})
    data = export_regression_suite(suite)
    assert isinstance(data, dict)
    restored = import_regression_suite(data)
    assert restored == suite


def test_save_and_load_suite(tmp_path) -> None:
    suite = RegressionSuite(name="s", cases=[_case()])
    path = tmp_path / "suite.json"
    save_regression_suite(suite, path)
    assert path.exists()
    assert load_regression_suite(path) == suite
