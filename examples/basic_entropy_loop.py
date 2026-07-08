"""A minimal, runnable example of the entropy loop.

Run it with::

    python examples/basic_entropy_loop.py

It defines a flaky agent that fails on its first attempt and succeeds on the
second, then prints the structured result along with the remembered failures.
"""

from __future__ import annotations

from entropy_loop_core import EntropyLoop, MemoryStore, Task, Verifier


def flaky_agent(task: Task, attempt: int) -> str:
    """Return an empty (failing) answer on attempt 1, a real answer after."""
    if attempt == 1:
        return ""
    return f"Answer for: {task.prompt}"


def main() -> None:
    """Run a single task through the loop and print the outcome."""
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=3)

    result = loop.run(Task(prompt="explain entropy loops"), flaky_agent)

    print(f"status:   {result.status.value}")
    print(f"attempts: {result.attempts}")
    print(f"output:   {result.output!r}")
    print("remembered failures:")
    for failure in memory.failures():
        print(f"  - attempt {failure.attempt}: {failure.reason}")


if __name__ == "__main__":
    main()
