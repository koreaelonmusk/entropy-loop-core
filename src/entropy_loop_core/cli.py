"""Minimal command-line interface for Entropy Loop Core.

Exposes an ``entropy-loop`` command with:

- ``demo`` — runs a small fake agent through the loop and narrates the full
  failure-compiler pipeline, including the failure category, fingerprint, an
  evaluation summary, and a generated regression case.
- ``doctor`` — runs a few basic health checks on the installed package.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import typer

from .evaluation import summarize
from .lessons import LessonGenerator
from .loop import EntropyLoop
from .memory import MemoryStore
from .memory_policy import LessonCompactor
from .regression import generate_regression_case
from .regression_pack import (
    RegressionPack,
    RegressionPackRunner,
    load_regression_pack,
    save_regression_pack,
    write_json_report,
    write_junit_report,
)
from .replay import RegressionRunner
from .types import (
    AgentOutput,
    FailureTrace,
    MemoryPolicy,
    RegressionCase,
    RegressionSuite,
    RetryContext,
    Task,
    VerificationResult,
)
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


@app.command(name="replay-demo")
def replay_demo() -> None:
    """Generate a regression case from a failure, then replay it as a suite."""
    task = Task(id="replay-001", instruction="report the job status")
    verifier = Verifier().require_non_empty().require_terms(["status"])

    # A past failure: the agent omitted the required term "status".
    bad_output = AgentOutput(content="Processing complete.")
    trace = FailureTrace(
        task=task,
        output=bad_output,
        verification_result=verifier.verify(bad_output),
        attempt=1,
    )
    case = generate_regression_case(trace)
    suite = RegressionSuite(name="job-status-regressions", cases=[case])

    typer.echo("Entropy Loop Replay Demo")
    typer.echo(f"1. Regression suite created: {suite.name!r}")
    typer.echo(f"2. Cases: {len(suite.cases)}")
    typer.echo(f"3. Replaying: {case.name}")

    # A corrected agent now includes the required term.
    def corrected_agent(task: Task, context: RetryContext) -> AgentOutput:
        return AgentOutput(content="status: ok - processing complete.")

    report = RegressionRunner().run_suite(suite, corrected_agent, verifier)

    outcome = "passed" if report.results[0].passed else "failed"
    typer.echo(f"4. Result: {outcome}")
    typer.echo(
        f"5. Report: total={report.total_cases}, passed={report.passed}, "
        f"failed={report.failed}, success_rate={report.success_rate}%"
    )

    if report.failed:
        raise typer.Exit(code=1)


def _memory_trace(
    instruction: str, reason: str, rule_name: str, category: str
) -> FailureTrace:
    """Build a fake failure trace for the memory demo."""
    return FailureTrace(
        task=Task(id="mem", instruction=instruction),
        output=AgentOutput(content=""),
        verification_result=VerificationResult(
            passed=False, reason=reason, rule_name=rule_name, category=category
        ),
        attempt=1,
    )


@app.command(name="memory-demo")
def memory_demo() -> None:
    """Generate repeated-failure lessons, then compact them with a MemoryPolicy."""
    generator = LessonGenerator()
    traces = [
        _memory_trace(
            "report the job status",
            "missing required terms: ['status']",
            "contains_required_terms",
            "missing_required_term",
        ),
        _memory_trace(
            "report the job status",
            "missing required terms: ['status']",
            "contains_required_terms",
            "missing_required_term",
        ),
        _memory_trace(
            "summarize the notes", "output is empty", "non_empty_output", "empty_output"
        ),
        _memory_trace(
            "summarize the notes", "output is empty", "non_empty_output", "empty_output"
        ),
        _memory_trace(
            "return the record as JSON",
            "expected valid JSON",
            "valid_json_when_expected",
            "invalid_json",
        ),
    ]
    lessons = [generator.generate(trace) for trace in traces]
    policy = MemoryPolicy(dedupe_by_fingerprint=True, max_lessons=3)
    result = LessonCompactor().compact(lessons, policy)

    typer.echo("Entropy Loop Memory Demo")
    typer.echo(f"1. Lessons generated: {len(lessons)}")
    typer.echo(
        "2. Policy: "
        f"dedupe_by_fingerprint={policy.dedupe_by_fingerprint}, "
        f"max_lessons={policy.max_lessons}"
    )
    typer.echo("3. Compaction complete")
    typer.echo(f"4. Input lessons: {result.input_count}")
    typer.echo(f"5. Output lessons: {result.output_count}")
    typer.echo(f"6. Dropped: {result.dropped_count}")
    typer.echo("7. Result: compacted memory ready")


def _demo_pack() -> RegressionPack:
    """Build a small, deterministic JSON-agent regression pack that passes."""
    policy = VerificationPolicy(require_non_empty=True, expect_json=True)
    cases = [
        RegressionCase(
            name="json-1",
            instruction="return the user record as JSON",
            expected_rule="valid_json_when_expected",
            failure_reason="expected valid JSON",
            category="invalid_json",
        ),
        RegressionCase(
            name="json-2",
            instruction="return the order as JSON",
            expected_rule="valid_json_when_expected",
            failure_reason="expected valid JSON",
            category="invalid_json",
        ),
        RegressionCase(
            name="json-3",
            instruction="return the status as JSON",
            expected_rule="valid_json_when_expected",
            failure_reason="expected valid JSON",
            category="invalid_json",
        ),
    ]
    outputs = {
        "json-1": '{"user": "ada"}',
        "json-2": '{"order": 42}',
        "json-3": '{"status": "ok"}',
    }
    return RegressionPack(
        name="json-agent-guard", policy=policy, cases=cases, outputs=outputs
    )


@app.command(name="pack-demo")
def pack_demo() -> None:
    """Create a regression pack, save it, load it, and run it."""
    pack = _demo_pack()
    typer.echo("Entropy Loop Regression Pack Demo")
    typer.echo(f"1. Pack created: {pack.name}")
    typer.echo(f"2. Cases: {len(pack.cases)}")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "pack.json"
        save_regression_pack(pack, path)
        typer.echo("3. Pack saved")
        loaded = load_regression_pack(path)
        typer.echo("4. Pack loaded")
        result = RegressionPackRunner().run_pack(loaded)

    typer.echo("5. Pack run complete")
    typer.echo(f"6. Passed: {result.passed_count}")
    typer.echo(f"7. Failed: {result.failed_count}")
    typer.echo("8. Result: regression pack ready for CI")

    if not result.success:
        raise typer.Exit(code=1)


@app.command(name="run-pack")
def run_pack(
    pack_path: str = typer.Argument(..., help="Path to a regression pack JSON file."),
    json_report: str = typer.Option(
        None, "--json-report", help="Write a JSON report to this path."
    ),
    junit_report: str = typer.Option(
        None, "--junit-report", help="Write a JUnit XML report to this path."
    ),
) -> None:
    """Run a regression pack. Exit 0 = all pass, 1 = a failure, 2 = bad input."""
    path = Path(pack_path)
    if not path.is_file():
        typer.echo(f"error: regression pack not found: {pack_path}", err=True)
        raise typer.Exit(code=2)
    try:
        pack = load_regression_pack(path)
    except Exception as exc:  # noqa: BLE001 - any load error is a usage error (exit 2)
        typer.echo(f"error: invalid regression pack: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    result = RegressionPackRunner().run_pack(pack)
    typer.echo(result.summary)

    if json_report:
        write_json_report(result, json_report)
        typer.echo(f"json report: {json_report}")
    if junit_report:
        write_junit_report(result, junit_report)
        typer.echo(f"junit report: {junit_report}")

    if not result.success:
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
