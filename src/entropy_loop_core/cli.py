"""Minimal command-line interface for Entropy Loop Core.

Exposes an ``entropy-loop`` command with a ``demo`` subcommand that runs a small
fake agent through the loop to illustrate the failure-then-retry behaviour.
"""

from __future__ import annotations

import typer

from .loop import EntropyLoop
from .memory import MemoryStore
from .types import LoopStatus, Task
from .verification import Verifier

app = typer.Typer(
    add_completion=False,
    help="Reliability layer for AI agents: remember, verify, retry.",
)


@app.callback()
def _root() -> None:
    """Entropy Loop Core command-line interface."""
    # Present so ``demo`` remains an explicit subcommand rather than collapsing
    # into the root command.


def _flaky_agent(task: Task, attempt: int) -> str:
    """A fake agent that fails on the first attempt and succeeds afterwards.

    It returns an empty string on attempt 1 (which fails the non-empty rule)
    and a real answer on later attempts.
    """
    if attempt == 1:
        return ""
    return f"Handled: {task.prompt}"


@app.command()
def demo() -> None:
    """Run a demo task that fails once, is remembered, retries, and succeeds."""
    memory = MemoryStore()
    loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=3)
    task = Task(prompt="summarize the release notes")

    typer.echo(f"Running task: {task.prompt!r}")
    result = loop.run(task, _flaky_agent)

    for failure in memory.failures():
        typer.echo(f"  attempt {failure.attempt} failed: {failure.reason}")

    typer.echo(f"Status:   {result.status.value}")
    typer.echo(f"Attempts: {result.attempts}")
    typer.echo(f"Output:   {result.output!r}")

    if result.status is not LoopStatus.SUCCESS:
        raise typer.Exit(code=1)


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
