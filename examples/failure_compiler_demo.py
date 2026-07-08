"""A runnable end-to-end example of the Failure Compiler (v0.2.0).

Run it with::

    python examples/failure_compiler_demo.py

It configures a verifier from a policy, defines an agent that omits a required
term on its first attempt, and runs the loop. The loop verifies the output,
classifies and traces the failure, compiles a lesson, and retries with the
lesson in context. The script then generates regression cases and prints an
evaluation summary of the run.
"""

from __future__ import annotations

from entropy_loop_core import (
    AgentOutput,
    EntropyLoop,
    MemoryStore,
    RetryContext,
    Task,
    VerificationPolicy,
    Verifier,
    export_regression_cases,
    generate_regression_case,
    summarize,
)


def learning_agent(task: Task, context: RetryContext) -> AgentOutput:
    """Omit the required term until a lesson has been fed back, then include it."""
    if not context.lessons:
        return AgentOutput(content="Job finished.")  # missing the term "status"
    return AgentOutput(content="status: done - job finished.")


def main() -> None:
    """Run one task through the compiler and print the compiled artifacts."""
    memory = MemoryStore()
    policy = VerificationPolicy(require_non_empty=True, required_terms=["status"])
    loop = EntropyLoop(
        verifier=Verifier.from_policy(policy), memory=memory, max_attempts=3
    )

    task = Task(id="demo-001", instruction="report the job status")
    result = loop.run(task, learning_agent)

    print(f"status:   {result.status}")
    print(f"attempts: {result.attempts}")
    output = result.output.content if result.output else None
    print(f"output:   {output!r}")

    print("\nfailure traces:")
    for trace in result.failures:
        print(f"  - attempt {trace.attempt} [{trace.category}] fp={trace.fingerprint}")
        print(f"      reason: {trace.verification_result.reason}")

    print("\ncompiled lessons:")
    for lesson in result.lessons:
        print(f"  - {lesson.summary}")
        print(f"      patch: {lesson.recommended_prompt_patch}")

    cases = [generate_regression_case(trace) for trace in result.failures]
    print("\nregression cases (exported):")
    for exported in export_regression_cases(cases):
        print(f"  - {exported}")

    summary = summarize(result, cases)
    print("\nevaluation summary:")
    print(f"  {summary.model_dump()}")


if __name__ == "__main__":
    main()
