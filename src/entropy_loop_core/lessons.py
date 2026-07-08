"""Deterministic compilation of failures into reusable lessons.

:class:`LessonGenerator` is the core of the *Failure Compiler*: it turns a
structured :class:`~entropy_loop_core.types.FailureTrace` into a reusable
:class:`~entropy_loop_core.types.Lesson`. It is rule-based and deterministic on
purpose — **no LLM, no network, no randomness** — so the same failure always
compiles to the same lesson and the behavior is fully testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import FailureTrace, Lesson


@dataclass(frozen=True)
class _Guidance:
    """Fixed advice attached to a specific verification-rule failure."""

    avoid: str
    patch: str
    tag: str


# Per-rule guidance: what advice a lesson should carry when that rule fails.
_TEMPLATES: dict[str, _Guidance] = {
    "non_empty_output": _Guidance(
        avoid="Do not return empty or whitespace-only content.",
        patch="Always produce a concrete, non-empty answer before returning.",
        tag="empty-output",
    ),
    "contains_required_terms": _Guidance(
        avoid="Do not omit the terms the task requires.",
        patch="Make sure every required term appears in the response.",
        tag="missing-terms",
    ),
    "valid_json_when_expected": _Guidance(
        avoid="Do not return malformed JSON when JSON output is expected.",
        patch="Return only valid, parseable JSON with no extra prose.",
        tag="invalid-json",
    ),
    "max_length": _Guidance(
        avoid="Do not exceed the allowed output length.",
        patch="Keep the response within the length limit; be concise.",
        tag="too-long",
    ),
    "agent_exception": _Guidance(
        avoid="Do not let unhandled errors escape the agent.",
        patch="Validate inputs and handle errors before producing output.",
        tag="agent-error",
    ),
}

_DEFAULT_TEMPLATE = _Guidance(
    avoid="Do not repeat the behavior that failed verification.",
    patch="Address the verification failure before retrying.",
    tag="general",
)


class LessonGenerator:
    """Compiles failure traces into reusable lessons using fixed rules.

    The generator is deterministic and side-effect free. It looks up guidance by
    the failed rule's name and always folds the task instruction into the
    lesson summary so the lesson can later be matched to similar tasks.
    """

    def generate(self, trace: FailureTrace) -> Lesson:
        """Compile a single failure trace into a lesson.

        Args:
            trace: The structured failure to learn from.

        Returns:
            A :class:`Lesson` summarizing the failure and how to avoid it.
        """
        rule_name = trace.verification_result.rule_name or "unknown"
        guidance = _TEMPLATES.get(rule_name, _DEFAULT_TEMPLATE)
        reason = trace.verification_result.reason or "verification failed"

        summary = (
            f"On task '{trace.task.instruction}', attempt {trace.attempt} "
            f"failed the '{rule_name}' check: {reason}."
        )

        return Lesson(
            summary=summary,
            avoid_next_time=guidance.avoid,
            recommended_prompt_patch=guidance.patch,
            tags=[guidance.tag, rule_name],
        )
