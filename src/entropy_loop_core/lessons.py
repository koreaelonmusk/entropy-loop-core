"""Deterministic compilation of failures into reusable lessons.

:class:`LessonGenerator` is the core of the *Failure Compiler*: it turns a
structured :class:`~entropy_loop_core.types.FailureTrace` into a reusable
:class:`~entropy_loop_core.types.Lesson`. Guidance is keyed by the failure's
:data:`~entropy_loop_core.types.FailureCategory`, so a whole class of failures
maps to consistent advice.

It is rule-based and deterministic on purpose — **no LLM, no network, no
randomness** — so the same failure always compiles to the same lesson and the
behavior is fully testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import FailureCategory, FailureTrace, Lesson


@dataclass(frozen=True)
class _Guidance:
    """Fixed advice attached to a specific failure category."""

    avoid: str
    patch: str


# Per-category guidance: the advice a lesson should carry for each failure kind.
_GUIDANCE: dict[FailureCategory, _Guidance] = {
    "empty_output": _Guidance(
        avoid="Do not return empty or whitespace-only content.",
        patch="Always produce a concrete, non-empty answer before returning.",
    ),
    "missing_required_term": _Guidance(
        avoid="Do not omit the terms the task requires.",
        patch="Make sure every required term appears in the response.",
    ),
    "invalid_json": _Guidance(
        avoid="Do not return malformed JSON when JSON output is expected.",
        patch="Return only valid, parseable JSON with no extra prose.",
    ),
    "too_long": _Guidance(
        avoid="Do not exceed the allowed output length.",
        patch="Keep the response within the length limit; be concise.",
    ),
    "agent_exception": _Guidance(
        avoid="Do not let unhandled errors escape the agent.",
        patch="Validate inputs and handle errors before producing output.",
    ),
    "unknown": _Guidance(
        avoid="Do not repeat the behavior that failed verification.",
        patch="Address the verification failure before retrying.",
    ),
}


class LessonGenerator:
    """Compiles failure traces into reusable lessons using fixed rules.

    The generator is deterministic and side-effect free. It selects guidance by
    the failure category and always folds the task instruction into the lesson
    summary so the lesson can later be matched to similar tasks.
    """

    def generate(self, trace: FailureTrace) -> Lesson:
        """Compile a single failure trace into a lesson.

        Args:
            trace: The structured failure to learn from.

        Returns:
            A :class:`Lesson` summarizing the failure and how to avoid it.
        """
        result = trace.verification_result
        category = result.category
        guidance = _GUIDANCE.get(category, _GUIDANCE["unknown"])
        reason = result.reason or "verification failed"

        summary = (
            f"On task '{trace.task.instruction}', attempt {trace.attempt} "
            f"failed with category '{category}': {reason}."
        )

        return Lesson(
            summary=summary,
            avoid_next_time=guidance.avoid,
            recommended_prompt_patch=guidance.patch,
            tags=[category, result.rule_name],
        )
