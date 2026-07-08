"""Tests for the deterministic, category-based lesson generator."""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    LessonGenerator,
    Task,
    VerificationResult,
)


def _trace(
    category: str, reason: str, rule_name: str = "some_rule", instruction: str = "do it"
) -> FailureTrace:
    return FailureTrace(
        task=Task(id="t", instruction=instruction),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason=reason, rule_name=rule_name, category=category
        ),
        attempt=2,
    )


def test_lesson_summary_includes_instruction_and_category() -> None:
    lesson = LessonGenerator().generate(
        _trace("empty_output", "output is empty", instruction="summarize notes")
    )
    assert "summarize notes" in lesson.summary
    assert "empty_output" in lesson.summary
    assert "output is empty" in lesson.summary


def test_guidance_differs_by_category() -> None:
    gen = LessonGenerator()
    empty = gen.generate(_trace("empty_output", "output is empty"))
    json_bad = gen.generate(_trace("invalid_json", "expected valid JSON"))
    assert empty.avoid_next_time != json_bad.avoid_next_time
    assert "empty_output" in empty.tags
    assert "invalid_json" in json_bad.tags


def test_generation_is_deterministic() -> None:
    trace = _trace("too_long", "output exceeds 5 characters")
    gen = LessonGenerator()
    assert gen.generate(trace) == gen.generate(trace)


def test_unknown_category_falls_back_to_default_guidance() -> None:
    lesson = LessonGenerator().generate(_trace("unknown", "something odd"))
    assert "unknown" in lesson.tags
    assert lesson.recommended_prompt_patch
