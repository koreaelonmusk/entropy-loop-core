"""Compact noisy failure lessons with a deterministic MemoryPolicy.

Run it with::

    python examples/memory_policy_guard.py

An agent repeatedly omits required fields, so the same failure happens again and
again. Each failure compiles to a lesson — and raw lesson memory quickly fills
with near-duplicates. A ``MemoryPolicy`` compacts that memory down to the
lessons that actually matter, deterministically: no LLM, no network, no database.
"""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    LessonCompactor,
    LessonGenerator,
    MemoryPolicy,
    Task,
    VerificationResult,
    export_compaction_result,
)


def _trace(
    instruction: str, reason: str, rule_name: str, category: str
) -> FailureTrace:
    return FailureTrace(
        task=Task(id="guard", instruction=instruction),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason=reason, rule_name=rule_name, category=category
        ),
        attempt=1,
    )


def main() -> None:
    """Generate repeated-failure lessons, then compact them."""
    generator = LessonGenerator()

    # The agent keeps omitting the required "status" field, plus some other noise.
    traces = [
        _trace(
            "emit the user record",
            "missing required terms: ['id']",
            "contains_required_terms",
            "missing_required_term",
        ),
        _trace(
            "emit the user record",
            "missing required terms: ['id']",
            "contains_required_terms",
            "missing_required_term",
        ),
        _trace(
            "emit the user record",
            "missing required terms: ['id']",
            "contains_required_terms",
            "missing_required_term",
        ),
        _trace(
            "emit the user record",
            "output is empty",
            "non_empty_output",
            "empty_output",
        ),
        _trace(
            "emit the user record",
            "expected valid JSON",
            "valid_json_when_expected",
            "invalid_json",
        ),
    ]
    lessons = [generator.generate(trace) for trace in traces]
    print(f"raw lessons: {len(lessons)}")

    # Keep one lesson per distinct guidance, cap at 3, drop empties.
    policy = MemoryPolicy(
        dedupe_by_fingerprint=True, max_lessons=3, drop_empty_lessons=True
    )
    result = LessonCompactor().compact(lessons, policy)

    print(f"compacted lessons: {result.output_count}")
    print(f"summary: {result.summary}")
    print(f"by category: {result.category_counts}")
    print(f"dropped reasons: {result.dropped_reasons}")

    print("\nkept lessons:")
    for lesson in result.lessons:
        print(f"  - {lesson.recommended_prompt_patch}  (tags={lesson.tags})")

    print("\nexported result:")
    print(f"  keys: {sorted(export_compaction_result(result))}")


if __name__ == "__main__":
    main()
