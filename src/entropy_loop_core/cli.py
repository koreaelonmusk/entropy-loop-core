"""Minimal command-line interface for Entropy Loop Core.

Exposes an ``entropy-loop`` command with a ``demo`` subcommand that runs a small
fake agent through the loop and narrates the full failure-compiler pipeline:
run, verify, trace, compile a lesson, retry with that lesson, and succeed.
"""

from __future__ import annotations

import typer

from .loop import EntropyLoop
from .memory import MemoryStore
from .types import AgentContext, AgentOutput, LoopStatus, Task
from .verification import Verifier

app = typer.Typer(
    add_completion=False,
    help="A Failure Compiler for AI agents: verify, trace, learn, retry.",
)


@app.callback()
def _root() -> None:
    """Entropy Loop Core command-line interface."""
    # Present so ``demo`` remains an explicit subcommand rather than collapsing
    # into the root command.


def _flaky_agent(context: AgentContext) -> AgentOutput:
    """A fake agent that fails until it has learned from a lesson.

    On the first attempt it has no lessons and returns empty content (which
    fails the non-empty rule). Once the loop has compiled a lesson from that
    failure and fed it back, the agent produces a real answer.
    """
    if not context.lessons:
        return AgentOutput(content="")
    return AgentOutput(content=f"Draft summary for: {context.task.instruction}")


@app.command()
def demo() -> None:
    """Run a task that fails once, is compiled into a lesson, then succeeds."""
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=3)
    task = Task(id="demo-001", instruction="summarize the release notes")

    typer.echo(f"▶ Task [{task.id}]: {task.instruction!r}")
    result = loop.run(task, _flaky_agent)

    for trace in result.failures:
        vr = trace.verification_result
        typer.echo(
            f"  ✗ attempt {trace.attempt} failed "
            f"[{vr.rule_name}/{vr.severity.value}]: {vr.reason}"
        )

    for lesson in result.lessons:
        typer.echo(f"  ⚙ compiled lesson: {lesson.summary}")
        typer.echo(f"      patch: {lesson.recommended_prompt_patch}")

    for case in result.regression_cases:
        typer.echo(f"  🧪 regression case: {case.name} (expects {case.expected_rule})")

    typer.echo("")
    typer.echo(f"Status:   {result.status.value}")
    typer.echo(f"Attempts: {result.attempts}")
    content = result.output.content if result.output else None
    typer.echo(f"Output:   {content!r}")

    if result.status is not LoopStatus.SUCCESS:
        raise typer.Exit(code=1)


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
