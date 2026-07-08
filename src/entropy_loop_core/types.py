"""Typed task and result objects for Entropy Loop Core.

These models define the data contract shared across the memory, verification,
and loop components. They are intentionally small and dependency-light so they
can be reused by callers building their own reliability tooling.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class LoopStatus(str, Enum):
    """Outcome of an :class:`~entropy_loop_core.loop.EntropyLoop` run."""

    SUCCESS = "success"
    FAILED = "failed"


class Task(BaseModel):
    """A unit of work handed to an agent.

    Attributes:
        prompt: The instruction or input the agent should act on.
        metadata: Optional free-form context attached to the task.
    """

    prompt: str = Field(..., description="Instruction or input for the agent.")
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Optional free-form context attached to the task.",
    )


class Failure(BaseModel):
    """A recorded failure produced during a loop attempt.

    Attributes:
        task_prompt: The prompt of the task that failed.
        attempt: The 1-based attempt number that produced the failure.
        reason: Human-readable explanation of why the attempt failed.
    """

    task_prompt: str = Field(..., description="Prompt of the task that failed.")
    attempt: int = Field(..., ge=1, description="1-based attempt number.")
    reason: str = Field(..., description="Why the attempt failed.")


class Lesson(BaseModel):
    """A distilled takeaway derived from one or more failures.

    Attributes:
        topic: Short key used to group related lessons.
        insight: The actionable guidance to apply on future attempts.
    """

    topic: str = Field(..., description="Short key grouping related lessons.")
    insight: str = Field(..., description="Actionable guidance for future attempts.")


class LoopResult(BaseModel):
    """Structured result of running a task through the entropy loop.

    Attributes:
        status: Whether the loop ultimately succeeded or failed.
        attempts: Total number of attempts made.
        output: The final agent output, if any.
        errors: Ordered list of failure reasons encountered along the way.
    """

    status: LoopStatus = Field(..., description="Final status of the loop.")
    attempts: int = Field(..., ge=0, description="Total number of attempts made.")
    output: str | None = Field(
        default=None, description="Final agent output, if the loop succeeded."
    )
    errors: list[str] = Field(
        default_factory=list, description="Failure reasons encountered, in order."
    )
