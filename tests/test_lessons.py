"""Tests for the deterministic lesson generator."""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    LessonGenerator,
    Task,
    VerificationResult,
)


def _trace(
    rule_name: str, reason: str, instruction: str = "do the thing"
) -> FailureTrace:
    return FailureTrace(
        task=Task(instruction=instruction),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason=reason, rule_name=rule_name
        ),
        attempt=2,
    )


def test_lesson_summary_includes_instruction_and_rule() -> None:
    lesson = LessonGenerator().generate(
        _trace("non_empty_output", "output is empty", instruction="summarize notes")
    )
    assert "summarize notes" in lesson.summary
    assert "non_empty_output" in lesson.summary
    assert "output is empty" in lesson.summary


def test_lesson_carries_rule_specific_guidance_and_tags() -> None:
    lesson = LessonGenerator().generate(_trace("non_empty_output", "output is empty"))
    assert lesson.avoid_next_time
    assert lesson.recommended_prompt_patch
    assert "empty-output" in lesson.tags
    assert "non_empty_output" in lesson.tags


def test_generation_is_deterministic() -> None:
    trace = _trace("max_length", "output exceeds 5 characters")
    gen = LessonGenerator()
    assert gen.generate(trace) == gen.generate(trace)


def test_unknown_rule_falls_back_to_default_guidance() -> None:
    lesson = LessonGenerator().generate(_trace("mystery_rule", "something odd"))
    assert "general" in lesson.tags
    assert "mystery_rule" in lesson.tags
    assert lesson.recommended_prompt_patch
