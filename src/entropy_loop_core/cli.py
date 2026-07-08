"""Minimal command-line interface for Entropy Loop Core.

Exposes an ``entropy-loop`` command with a ``demo`` subcommand that runs a small
fake agent through the loop and narrates the full failure-compiler pipeline:
run, verify, trace, compile a lesson, retry with that lesson, and succeed.
"""

from __future__ import annotations

import typer

from .loop import EntropyLoop
from .memory import MemoryStore
from .types import AgentOutput, RetryContext, Task
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


def _demo_agent(task: Task, context: RetryContext) -> AgentOutput:
    """A fake agent that fails until it has learned from a lesson.

    On the first attempt it has no lessons and omits the required term
    ``"status"`` (failing verification). Once the loop has compiled a lesson
    from that failure and fed it back, the agent includes the term and passes.
    """
    if not context.lessons:
        return AgentOutput(content="Processing complete.")
    return AgentOutput(content="status: ok - processing complete.")


@app.command()
def demo() -> None:
    """Run a task that fails once, is compiled into a lesson, then succeeds."""
    memory = MemoryStore()
    verifier = Verifier().require_non_empty().require_terms(["status"])
    loop = EntropyLoop(verifier=verifier, memory=memory, max_attempts=3)
    task = Task(id="demo-001", instruction="report the job status")

    typer.echo("Entropy Loop Demo")
    typer.echo("1. Running task...")

    result = loop.run(task, _demo_agent)

    for failure in result.failures:
        typer.echo(
            f"2. Attempt {failure.attempt} failed: {failure.verification_result.reason}"
        )
        typer.echo("3. Failure trace stored")
        typer.echo("4. Lesson generated")
        typer.echo("5. Retrying with lesson context")

    if result.status == "success":
        typer.echo(f"6. Attempt {result.attempts} passed")
        typer.echo("7. Loop completed successfully")
        content = result.output.content if result.output else ""
        typer.echo(f"   Output: {content!r}")
    else:
        typer.echo(f"6. Gave up after {result.attempts} attempts")
        raise typer.Exit(code=1)


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
