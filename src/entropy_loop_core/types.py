"""Typed data contract for Entropy Loop Core.

These Pydantic models are the shared vocabulary of the *Failure Compiler*: a
task flows in, an agent produces output, a verifier judges it and classifies any
failure, and that failure is captured as a structured :class:`FailureTrace` that
can be fingerprinted, compiled into a reusable :class:`Lesson`, turned into a
:class:`RegressionCase`, and rolled up into an :class:`EvaluationSummary`.

The models are intentionally small and dependency-light so they can be reused by
callers building their own reliability tooling.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

# Severity of a verification failure, from advisory to blocking.
Severity = Literal["info", "warning", "error", "critical"]

# Final status of an entropy-loop run.
Status = Literal["success", "failed"]

# A small, deliberately non-exhaustive set of public-safe failure categories.
# This is a starting taxonomy, not a universal one.
FailureCategory = Literal[
    "empty_output",
    "missing_required_term",
    "invalid_json",
    "too_long",
    "agent_exception",
    "unknown",
]


class Task(BaseModel):
    """A unit of work given to an AI agent.

    Attributes:
        id: Stable identifier for the task.
        instruction: The instruction or input the agent should act on.
        metadata: Optional free-form context (for example ``{"format": "json"}``).
    """

    id: str = Field(..., description="Stable identifier for the task.")
    instruction: str = Field(..., description="Instruction or input for the agent.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional free-form context attached to the task.",
    )


class AgentOutput(BaseModel):
    """The raw response produced by an agent for a single attempt.

    Attributes:
        content: The textual output the agent returned.
        metadata: Optional free-form context about how it was produced.
    """

    content: str = Field(..., description="Raw textual output from the agent.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional free-form context about the output.",
    )


class VerificationResult(BaseModel):
    """The verdict of checking a single agent output against a rule.

    Beyond pass/fail, a result explains *what kind* of failure happened via
    ``category`` and carries structured, public-safe context in ``details``.

    Attributes:
        passed: ``True`` when the checked output satisfied the rule(s).
        reason: Explanation of the outcome; empty when ``passed`` is ``True``.
        rule_name: Name of the rule that produced this result.
        severity: How serious the failure is; ignored when ``passed`` is True.
        category: The kind of failure; ``"unknown"`` when passed.
        details: Structured, non-sensitive context about the failure.
    """

    passed: bool = Field(..., description="Whether verification passed.")
    reason: str = Field(default="", description="Explanation of the outcome.")
    rule_name: str = Field(
        default="", description="Name of the rule that produced this result."
    )
    severity: Severity = Field(default="error", description="Severity of the failure.")
    category: FailureCategory = Field(
        default="unknown", description="The kind of failure that occurred."
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Structured, non-sensitive failure context."
    )


class FailureTrace(BaseModel):
    """A structured memory of one failed agent attempt.

    A ``FailureTrace`` is the atom the compiler works on. Its ``category`` and
    ``fingerprint`` are derived deterministically so similar failures can be
    grouped without storing anything sensitive — the fingerprint is a hash, not
    raw content.

    Attributes:
        task: The task that failed.
        output: The agent output that was rejected.
        verification_result: Why the output was rejected.
        attempt: The 1-based attempt number that produced the failure.
        timestamp: When the failure was recorded (UTC).
    """

    task: Task = Field(..., description="The task that failed.")
    output: AgentOutput = Field(..., description="The rejected agent output.")
    verification_result: VerificationResult = Field(
        ..., description="Why the output was rejected."
    )
    attempt: int = Field(..., ge=1, description="1-based attempt number.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the failure was recorded (UTC).",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def category(self) -> FailureCategory:
        """The failure category, taken from the verification result."""
        return self.verification_result.category

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fingerprint(self) -> str:
        """A deterministic, public-safe hash grouping similar failures.

        Derived from a hash of the task instruction plus the rule name,
        category, and reason. It contains no raw private content.
        """
        instruction_hash = hashlib.sha256(
            self.task.instruction.encode("utf-8")
        ).hexdigest()[:16]
        basis = "|".join(
            [
                instruction_hash,
                self.verification_result.rule_name,
                self.verification_result.category,
                self.verification_result.reason,
            ]
        )
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


class Lesson(BaseModel):
    """A compressed, reusable lesson derived from a failure.

    Attributes:
        summary: What went wrong, in one human-readable line.
        avoid_next_time: The behavior the agent should avoid on future attempts.
        recommended_prompt_patch: A concrete instruction to add on retry.
        tags: Short keys used to match this lesson to future tasks.
    """

    summary: str = Field(..., description="What went wrong, in one line.")
    avoid_next_time: str = Field(..., description="Behavior to avoid next time.")
    recommended_prompt_patch: str = Field(
        ..., description="Concrete instruction to add on retry."
    )
    tags: list[str] = Field(
        default_factory=list, description="Keys for matching to future tasks."
    )


class RetryContext(BaseModel):
    """Context passed into a retry attempt.

    On the first attempt this carries no prior failures or lessons; on retries
    it accumulates them so the agent can adapt its behavior.

    Attributes:
        attempt: The 1-based attempt number.
        prior_failures: Failure traces from earlier attempts, in order.
        lessons: Lessons relevant to this task, most recent last.
    """

    attempt: int = Field(..., ge=1, description="1-based attempt number.")
    prior_failures: list[FailureTrace] = Field(
        default_factory=list, description="Failures from earlier attempts."
    )
    lessons: list[Lesson] = Field(
        default_factory=list, description="Lessons relevant to this task."
    )


class LoopResult(BaseModel):
    """The final result of an entropy-loop run.

    Attributes:
        status: ``"success"`` or ``"failed"``.
        attempts: Total number of attempts made.
        output: The final agent output, if the loop succeeded.
        failures: The failure traces captured along the way, in order.
        lessons: The lessons compiled from those failures, in order.
        errors: Flat list of failure reasons, for quick inspection.
    """

    status: Status = Field(..., description="Final status of the loop.")
    attempts: int = Field(..., ge=0, description="Total number of attempts made.")
    output: AgentOutput | None = Field(
        default=None, description="Final agent output, if the loop succeeded."
    )
    failures: list[FailureTrace] = Field(
        default_factory=list, description="Failure traces captured, in order."
    )
    lessons: list[Lesson] = Field(
        default_factory=list, description="Lessons compiled from failures."
    )
    errors: list[str] = Field(
        default_factory=list, description="Failure reasons, for quick inspection."
    )


class RegressionCase(BaseModel):
    """A test-like artifact generated from a failure.

    A ``RegressionCase`` records a task that once failed together with the rule
    that must pass for the failure to be considered fixed, so the same mistake
    can be checked later.

    Attributes:
        name: A stable, identifier-friendly name for the case.
        instruction: The task instruction that triggered the failure.
        expected_rule: The verification rule that must now pass.
        failure_reason: The original failure message.
        category: The failure category the case guards against.
    """

    name: str = Field(..., description="Identifier-friendly name for the case.")
    instruction: str = Field(..., description="Instruction that triggered failure.")
    expected_rule: str = Field(..., description="Rule that must now pass.")
    failure_reason: str = Field(..., description="The original failure message.")
    category: FailureCategory = Field(
        default="unknown", description="Failure category the case guards against."
    )


class EvaluationSummary(BaseModel):
    """A compact, public-safe summary of a single loop run.

    Attributes:
        total_attempts: How many attempts the loop made.
        success: Whether the loop ultimately succeeded.
        failure_count: How many failures were captured.
        categories: Count of failures by category.
        final_status: The loop's final status.
        generated_regression_cases: How many regression cases were generated.
    """

    total_attempts: int = Field(..., ge=0, description="Attempts the loop made.")
    success: bool = Field(..., description="Whether the loop succeeded.")
    failure_count: int = Field(..., ge=0, description="Failures captured.")
    categories: dict[str, int] = Field(
        default_factory=dict, description="Count of failures by category."
    )
    final_status: Status = Field(..., description="The loop's final status.")
    generated_regression_cases: int = Field(
        default=0, ge=0, description="Regression cases generated from failures."
    )


class RegressionSuite(BaseModel):
    """A named collection of regression cases that can be replayed together.

    Attributes:
        name: A human-readable name for the suite.
        cases: The regression cases in the suite.
        metadata: Optional free-form context about the suite.
    """

    name: str = Field(..., description="Human-readable name for the suite.")
    cases: list[RegressionCase] = Field(
        default_factory=list, description="Regression cases in the suite."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional free-form context."
    )


class RegressionRunResult(BaseModel):
    """The outcome of replaying a single regression case.

    Attributes:
        case: The regression case that was replayed.
        passed: Whether the replayed output satisfied verification.
        output: The agent output produced during replay, if any.
        verification_result: The verdict of verifying the output, if reached.
        error: An error message if the agent raised during replay.
    """

    case: RegressionCase = Field(..., description="The replayed regression case.")
    passed: bool = Field(..., description="Whether the replay passed.")
    output: AgentOutput | None = Field(
        default=None, description="Agent output produced during replay."
    )
    verification_result: VerificationResult | None = Field(
        default=None, description="Verdict of verifying the output."
    )
    error: str | None = Field(
        default=None, description="Error message if the agent raised."
    )


class RegressionReport(BaseModel):
    """A summary of replaying a whole regression suite.

    Attributes:
        suite_name: The name of the suite that was replayed.
        total_cases: How many cases were replayed.
        passed: How many cases passed.
        failed: How many cases failed.
        results: The per-case results, in order.
    """

    suite_name: str = Field(..., description="Name of the replayed suite.")
    total_cases: int = Field(..., ge=0, description="Cases replayed.")
    passed: int = Field(..., ge=0, description="Cases that passed.")
    failed: int = Field(..., ge=0, description="Cases that failed.")
    results: list[RegressionRunResult] = Field(
        default_factory=list, description="Per-case results, in order."
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def success_rate(self) -> float:
        """Percentage of cases that passed, from 0.0 to 100.0."""
        if self.total_cases == 0:
            return 0.0
        return round(self.passed / self.total_cases * 100, 1)
