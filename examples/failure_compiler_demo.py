"""A runnable end-to-end example of the Failure Compiler.

Run it with::

    python examples/failure_compiler_demo.py

It defines an agent that omits a required term on its first attempt. The loop
verifies the output, traces the failure, compiles a lesson, and retries with the
lesson in context — at which point the agent adapts and succeeds. The script
then generates a regression case from the failure.
"""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    EntropyLoop,
    MemoryStore,
    RetryContext,
    Task,
    Verifier,
    generate_regression_case,
)


def learning_agent(task: Task, context: RetryContext) -> AgentOutput:
    """Omit the required term until a lesson has been fed back, then include it."""
    if not context.lessons:
        return AgentOutput(content="Job finished.")  # missing the term "status"
    return AgentOutput(content="status: done - job finished.")


def main() -> None:
    """Run one task through the compiler and print the compiled artifacts."""
    memory = MemoryStore()
    verifier = Verifier().require_non_empty().require_terms(["status"])
    loop = EntropyLoop(verifier=verifier, memory=memory, max_attempts=3)

    task = Task(id="demo-001", instruction="report the job status")
    result = loop.run(task, learning_agent)

    print(f"status:   {result.status}")
    print(f"attempts: {result.attempts}")
    output = result.output.content if result.output else None
    print(f"output:   {output!r}")

    print("\nfailure traces:")
    for trace in result.failures:
        vr = trace.verification_result
        print(f"  - attempt {trace.attempt} [{vr.rule_name}]: {vr.reason}")

    print("\ncompiled lessons:")
    for lesson in result.lessons:
        print(f"  - {lesson.summary}")
        print(f"      patch: {lesson.recommended_prompt_patch}")

    print("\nregression cases (generated from failures):")
    for trace in result.failures:
        case = generate_regression_case(trace)
        print(f"  - {case.name} (must pass: {case.expected_rule})")


if __name__ == "__main__":
    main()
