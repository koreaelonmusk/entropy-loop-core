"""Agent adapters and live pack refresh.

Where `run-pack` (v0.5.0) checks the candidate outputs stored in a pack, this
module lets you refresh those outputs from your **current** agent — explicitly.
An :class:`AgentAdapter` produces an output for a regression case;
:class:`CommandAgentAdapter` does so by running a local command you supply; and
:class:`RegressionPackRefresher` writes the fresh outputs into a new pack that
`run-pack` can then gate.

Security boundary — Entropy Loop Core executes a command **only** when you pass
one. There is no implicit execution, no auto-discovery, no shell by default, and
no secret injection. The library itself makes no network calls; a command you
provide may do its own I/O, and that is your responsibility.

The framework is deterministic given an adapter's outputs. The adapter's outputs
themselves depend on the command you run, so `refresh-pack` is only as
deterministic as your agent; `run-pack` remains fully deterministic.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from .regression_pack import (
    RegressionPack,
    load_regression_pack,
    save_regression_pack,
)
from .types import RegressionCase

# Environment keys copied into a command's environment by default. This keeps
# commands runnable (they can find an interpreter) without dumping the full
# process environment, which may hold secrets. Opt into the full environment
# with inherit_env=True.
_SAFE_ENV_KEYS = (
    "PATH",
    "HOME",
    "SYSTEMROOT",
    "SystemRoot",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TEMP",
    "TMP",
    "PYTHONPATH",
)


class AgentCommand(BaseModel):
    """An explicit local command to run an agent for a case.

    Attributes:
        argv: The command and its arguments (non-empty). Run without a shell.
        cwd: Working directory, or ``None`` for the current directory.
        timeout_seconds: Per-case timeout (> 0).
        env: Explicit environment overlay applied on top of a minimal base.
        stdin_template: Optional stdin format string (``{case_id}`` / ``{task}``);
            when omitted, the case input is sent to stdin as JSON.
    """

    argv: list[str] = Field(..., min_length=1, description="Command and arguments.")
    cwd: str | None = Field(default=None, description="Working directory.")
    timeout_seconds: int = Field(default=30, gt=0, description="Per-case timeout.")
    env: dict[str, str] = Field(default_factory=dict, description="Env overlay.")
    stdin_template: str | None = Field(default=None, description="stdin template.")


class AgentRunInput(BaseModel):
    """The input handed to an agent command for one regression case."""

    case_id: str = Field(..., description="The case identifier.")
    task: str = Field(..., description="The task instruction.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Context.")


class AgentRunResult(BaseModel):
    """The outcome of running an agent for one case.

    Attributes:
        case_id: The case identifier.
        stdout: Captured standard output.
        stderr: Captured standard error.
        exit_code: The process exit code (``-1`` on timeout).
        timed_out: Whether the command exceeded its timeout.
        duration_ms: How long the command took, in milliseconds.
        output: The candidate output (from stdout by default).
        success: True when the command exited 0 and did not time out.
    """

    case_id: str = Field(..., description="The case identifier.")
    stdout: str = Field(default="", description="Captured stdout.")
    stderr: str = Field(default="", description="Captured stderr.")
    exit_code: int = Field(..., description="Process exit code.")
    timed_out: bool = Field(default=False, description="Whether it timed out.")
    duration_ms: int | None = Field(default=None, description="Duration in ms.")
    output: str = Field(default="", description="Candidate output.")
    success: bool = Field(..., description="True on exit 0 without timeout.")


@runtime_checkable
class AgentAdapter(Protocol):
    """Produces a candidate output for a regression case."""

    def run_case(self, case: RegressionCase) -> AgentRunResult:
        """Run the agent for ``case`` and return its result."""
        ...


class CommandAgentAdapter:
    """An :class:`AgentAdapter` that runs a local :class:`AgentCommand`.

    Runs the command with a subprocess — **no shell** — enforces the timeout,
    captures stdout/stderr, and derives the candidate output from stdout. It does
    not raise on a non-zero agent exit; the failure is reported in the result.
    """

    def __init__(self, command: AgentCommand, inherit_env: bool = False) -> None:
        """Create the adapter.

        Args:
            command: The command to run per case.
            inherit_env: When True, pass the full process environment to the
                command; otherwise pass only a minimal, functional base.
        """
        self._command = command
        self._inherit_env = inherit_env

    def _build_env(self) -> dict[str, str]:
        if self._inherit_env:
            env = dict(os.environ)
        else:
            env = {key: os.environ[key] for key in _SAFE_ENV_KEYS if key in os.environ}
        env.update(self._command.env)
        return env

    def _stdin_for(self, run_input: AgentRunInput) -> str:
        if self._command.stdin_template is not None:
            return self._command.stdin_template.format(
                case_id=run_input.case_id, task=run_input.task
            )
        return json.dumps(run_input.model_dump())

    def run_case(self, case: RegressionCase) -> AgentRunResult:
        """Run the command for ``case`` and capture its output."""
        run_input = AgentRunInput(
            case_id=case.name,
            task=case.instruction,
            metadata={"category": case.category, "expected_rule": case.expected_rule},
        )
        started = time.monotonic()
        try:
            proc = subprocess.run(  # noqa: S603 - argv is explicit and shell=False
                self._command.argv,
                cwd=self._command.cwd,
                env=self._build_env(),
                input=self._stdin_for(run_input),
                capture_output=True,
                text=True,
                timeout=self._command.timeout_seconds,
                shell=False,
                check=False,
            )
            duration_ms = int((time.monotonic() - started) * 1000)
            return AgentRunResult(
                case_id=case.name,
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                timed_out=False,
                duration_ms=duration_ms,
                output=proc.stdout,
                success=proc.returncode == 0,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            return AgentRunResult(
                case_id=case.name,
                stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
                stderr=exc.stderr or "" if isinstance(exc.stderr, str) else "",
                exit_code=-1,
                timed_out=True,
                duration_ms=duration_ms,
                output="",
                success=False,
            )


class PackRefreshResult(BaseModel):
    """The outcome of refreshing a pack's outputs from an agent.

    Attributes:
        pack_name: The pack that was refreshed.
        case_count: How many cases the pack had.
        refreshed_count: How many outputs were refreshed.
        failed_count: How many agent runs failed.
        skipped_count: Cases not run (e.g. after a fail-fast stop).
        success: True when no agent run failed.
        outputs: The refreshed outputs by case id.
        summary: A deterministic one-line summary.
    """

    pack_name: str = Field(..., description="The refreshed pack name.")
    case_count: int = Field(..., ge=0, description="Cases in the pack.")
    refreshed_count: int = Field(..., ge=0, description="Outputs refreshed.")
    failed_count: int = Field(..., ge=0, description="Agent runs that failed.")
    skipped_count: int = Field(default=0, ge=0, description="Cases not run.")
    success: bool = Field(..., description="True when no run failed.")
    outputs: dict[str, str] = Field(
        default_factory=dict, description="Refreshed outputs by case id."
    )
    summary: str = Field(..., description="Deterministic one-line summary.")


class RegressionPackRefresher:
    """Refreshes a pack's candidate outputs using an :class:`AgentAdapter`."""

    def refresh_pack(
        self,
        pack: RegressionPack,
        adapter: AgentAdapter,
        fail_fast: bool = False,
    ) -> tuple[RegressionPack, PackRefreshResult]:
        """Refresh every case's output; return a new pack and a result.

        The original pack is not mutated. Metadata and verification policy are
        preserved; only ``outputs`` change.
        """
        outputs = dict(pack.outputs)
        refreshed = failed = 0
        ran = 0
        for case in pack.cases:
            ran += 1
            result = adapter.run_case(case)
            if result.success:
                outputs[case.name] = result.output
                refreshed += 1
            else:
                failed += 1
                if fail_fast:
                    break

        skipped = len(pack.cases) - ran
        new_pack = pack.model_copy(update={"outputs": outputs})
        summary = (
            f"Refreshed pack `{pack.name}`: {refreshed} refreshed, "
            f"{failed} failed, {skipped} skipped."
        )
        result_model = PackRefreshResult(
            pack_name=pack.name,
            case_count=len(pack.cases),
            refreshed_count=refreshed,
            failed_count=failed,
            skipped_count=skipped,
            success=failed == 0,
            outputs=outputs,
            summary=summary,
        )
        return new_pack, result_model

    def refresh_pack_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
        adapter: AgentAdapter,
        fail_fast: bool = False,
    ) -> PackRefreshResult:
        """Load a pack, refresh it, and write the refreshed pack to a file."""
        pack = load_regression_pack(input_path)
        new_pack, result = self.refresh_pack(pack, adapter, fail_fast)
        save_regression_pack(new_pack, output_path)
        return result


def export_refresh_report(result: PackRefreshResult) -> dict[str, Any]:
    """Render a compact, machine-readable JSON report of a pack refresh."""
    return {
        "pack": result.pack_name,
        "cases": result.case_count,
        "refreshed": result.refreshed_count,
        "failed": result.failed_count,
        "skipped": result.skipped_count,
        "success": result.success,
        "summary": result.summary,
    }


def write_refresh_report(result: PackRefreshResult, path: str | Path) -> None:
    """Write a refresh JSON report to ``path`` (creating parent directories)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(export_refresh_report(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
