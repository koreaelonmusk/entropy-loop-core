"""A runnable end-to-end example of the Failure Compiler.

Run it with::

    python examples/failure_compiler_demo.py

It defines an agent that returns empty output on its first attempt. The loop
verifies the output, traces the failure, compiles a lesson, generates a
regression case, and retries with the lesson in context — at which point the
agent adapts and succeeds. The script prints every compiled artifact.
"""

from __future__ import annotations

from entropy_loop_core import (
    AgentContext,
    AgentOutput,
    EntropyLoop,
    MemoryStore,
    Task,
    Verifier,
)


def learning_agent(context: AgentContext) -> AgentOutput:
    """Return empty (failing) output until a lesson has been fed back."""
    if not context.lessons:
        return AgentOutput(content="")
    return AgentOutput(content=f"Answer for: {context.task.instruction}")


def main() -> None:
    """Run one task through the compiler and print the compiled artifacts."""
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=3)

    task = Task(id="demo-001", instruction="explain entropy loops")
    result = loop.run(task, learning_agent)

    print(f"status:   {result.status.value}")
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
        print(f"      avoid: {lesson.avoid_next_time}")
        print(f"      patch: {lesson.recommended_prompt_patch}")

    print("\nregression cases:")
    for case in result.regression_cases:
        print(f"  - {case.name} (must pass: {case.expected_rule})")


if __name__ == "__main__":
    main()
