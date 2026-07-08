"""Minimal command-line interface for Entropy Loop Core.

Exposes an ``entropy-loop`` command with:

- ``demo`` — runs a small fake agent through the loop and narrates the full
  failure-compiler pipeline, including the failure category, fingerprint, an
  evaluation summary, and a generated regression case.
- ``doctor`` — runs a few basic health checks on the installed package.
"""

from __future__ import annotations

import typer

from .evaluation import summarize
from .loop import EntropyLoop
from .memory import MemoryStore
from .regression import generate_regression_case
from .types import AgentOutput, RetryContext, Task
from .verification import VerificationPolicy, Verifier

app = typer.Typer(
    add_completion=False,
    help="A Failure Compiler for AI agents: classify, trace, learn, retry.",
)


@app.callback()
def _root() -> None:
    """Entropy Loop Core command-line interface."""
    # Present so subcommands stay explicit rather than collapsing into the root.


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
    """Run a task that fails once, is classified and compiled, then succeeds."""
    memory = MemoryStore()
    policy = VerificationPolicy(require_non_empty=True, required_terms=["status"])
    loop = EntropyLoop(
        verifier=Verifier.from_policy(policy), memory=memory, max_attempts=3
    )
    task = Task(id="demo-001", instruction="report the job status")

    typer.echo("Entropy Loop Demo")
    typer.echo(f"1. Task started: {task.instruction!r}")

    result = loop.run(task, _demo_agent)

    for failure in result.failures:
        vr = failure.verification_result
        typer.echo(f"2. Attempt {failure.attempt} failed: {vr.reason}")
        typer.echo(f"3. Failure category: {failure.category}")
        typer.echo(f"4. Failure fingerprint: {failure.fingerprint}")
        typer.echo("5. Lesson generated")
        typer.echo("6. Retry context updated")

    if result.status == "success":
        typer.echo(f"7. Attempt {result.attempts} passed")

    cases = [generate_regression_case(trace) for trace in result.failures]
    evaluation = summarize(result, cases)

    typer.echo(
        "8. Evaluation summary: "
        f"status={evaluation.final_status}, attempts={evaluation.total_attempts}, "
        f"failures={evaluation.failure_count}, categories={evaluation.categories}"
    )
    for case in cases:
        typer.echo(f"9. Regression case generated: {case.name}")

    if result.status != "success":
        raise typer.Exit(code=1)


@app.command()
def doctor() -> None:
    """Run basic health checks: import, verifier, and a demo loop."""
    ok = True

    try:
        from . import __version__

        typer.echo(f"[ok] package import (v{__version__})")
    except Exception as exc:  # noqa: BLE001 - report any failure to the user
        ok = False
        typer.echo(f"[fail] package import: {exc}")

    try:
        result = Verifier().require_non_empty().verify(AgentOutput(content="hi"))
        assert result.passed
        typer.echo("[ok] verifier basic rule")
    except Exception as exc:  # noqa: BLE001 - report any failure to the user
        ok = False
        typer.echo(f"[fail] verifier basic rule: {exc}")

    try:
        loop = EntropyLoop(
            verifier=Verifier().require_non_empty(),
            memory=MemoryStore(),
            max_attempts=1,
        )
        run = loop.run(
            Task(id="doctor", instruction="ping"),
            lambda task, ctx: AgentOutput(content="pong"),
        )
        assert run.status == "success"
        typer.echo("[ok] demo loop")
    except Exception as exc:  # noqa: BLE001 - report any failure to the user
        ok = False
        typer.echo(f"[fail] demo loop: {exc}")

    if ok:
        typer.echo("All checks passed.")
    else:
        raise typer.Exit(code=1)


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
