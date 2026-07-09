"""Tests for agent adapters and live pack refresh."""

from __future__ import annotations

import sys

import pytest

from entropy_loop_core import (
    AgentCommand,
    AgentRunResult,
    CommandAgentAdapter,
    PackRefreshResult,
    RegressionCase,
    RegressionPack,
    RegressionPackRefresher,
    RegressionPackRunner,
    VerificationPolicy,
    export_refresh_report,
    load_regression_pack,
    save_regression_pack,
    write_refresh_report,
)

# A tiny deterministic agent: emit valid JSON to stdout.
_GOOD_AGENT = "import sys, json; sys.stdin.read(); print(json.dumps({'ok': True}))"
# An agent that exits non-zero.
_BAD_AGENT = "import sys; sys.stdin.read(); sys.exit(3)"


def _cmd(script: str, timeout: int = 30) -> AgentCommand:
    return AgentCommand(argv=[sys.executable, "-c", script], timeout_seconds=timeout)


def _case(name: str) -> RegressionCase:
    return RegressionCase(
        name=name,
        instruction=f"return {name} as JSON",
        expected_rule="valid_json_when_expected",
        failure_reason="expected valid JSON",
        category="invalid_json",
    )


def _pack() -> RegressionPack:
    return RegressionPack(
        name="json-agent-guard",
        policy=VerificationPolicy(require_non_empty=True, expect_json=True),
        cases=[_case("a"), _case("b")],
        outputs={"a": "old", "b": "old"},
        metadata={"origin": "test"},
    )


# --- AgentCommand ---------------------------------------------------------


def test_agent_command_valid() -> None:
    cmd = AgentCommand(argv=["echo", "hi"])
    assert cmd.timeout_seconds == 30
    assert cmd.env == {}


def test_agent_command_rejects_empty_argv() -> None:
    with pytest.raises(ValueError):
        AgentCommand(argv=[])


def test_agent_command_rejects_bad_timeout() -> None:
    with pytest.raises(ValueError):
        AgentCommand(argv=["echo"], timeout_seconds=0)


def test_agent_command_env_preserved() -> None:
    cmd = AgentCommand(argv=["echo"], env={"FOO": "bar"})
    assert cmd.env["FOO"] == "bar"


# --- CommandAgentAdapter --------------------------------------------------


def test_adapter_captures_stdout() -> None:
    result = CommandAgentAdapter(_cmd(_GOOD_AGENT)).run_case(_case("a"))
    assert isinstance(result, AgentRunResult)
    assert result.success is True
    assert result.exit_code == 0
    assert '"ok": true' in result.output


def test_adapter_records_nonzero_exit() -> None:
    result = CommandAgentAdapter(_cmd(_BAD_AGENT)).run_case(_case("a"))
    assert result.success is False
    assert result.exit_code == 3


def test_adapter_handles_timeout() -> None:
    slow = "import time, sys; sys.stdin.read(); time.sleep(5)"
    result = CommandAgentAdapter(_cmd(slow, timeout=1)).run_case(_case("a"))
    assert result.timed_out is True
    assert result.success is False


def test_adapter_captures_stderr() -> None:
    err = "import sys; sys.stdin.read(); sys.stderr.write('boom'); print('{}')"
    result = CommandAgentAdapter(_cmd(err)).run_case(_case("a"))
    assert "boom" in result.stderr
    assert result.success is True


# --- RegressionPackRefresher ----------------------------------------------


def test_refresh_updates_outputs_and_preserves_pack() -> None:
    pack = _pack()
    new_pack, result = RegressionPackRefresher().refresh_pack(
        pack, CommandAgentAdapter(_cmd(_GOOD_AGENT))
    )
    assert isinstance(result, PackRefreshResult)
    assert result.refreshed_count == 2
    assert result.failed_count == 0
    assert result.success is True
    # outputs updated by case id
    assert '"ok": true' in new_pack.outputs["a"]
    # metadata and policy preserved; original pack unchanged
    assert new_pack.metadata == {"origin": "test"}
    assert new_pack.policy == pack.policy
    assert pack.outputs == {"a": "old", "b": "old"}


def test_refresh_records_failure() -> None:
    _, result = RegressionPackRefresher().refresh_pack(
        _pack(), CommandAgentAdapter(_cmd(_BAD_AGENT))
    )
    assert result.failed_count == 2
    assert result.success is False


def test_refresh_fail_fast_skips_remaining() -> None:
    _, result = RegressionPackRefresher().refresh_pack(
        _pack(), CommandAgentAdapter(_cmd(_BAD_AGENT)), fail_fast=True
    )
    assert result.failed_count == 1
    assert result.skipped_count == 1


def test_refresh_summary_is_deterministic() -> None:
    refresher = RegressionPackRefresher()
    adapter = CommandAgentAdapter(_cmd(_GOOD_AGENT))
    a = refresher.refresh_pack(_pack(), adapter)[1].summary
    b = refresher.refresh_pack(_pack(), adapter)[1].summary
    assert a == b
    assert "2 refreshed" in a


def test_refresh_pack_file_then_run(tmp_path) -> None:
    src = tmp_path / "in.pack.json"
    dst = tmp_path / "out.pack.json"
    save_regression_pack(_pack(), src)
    result = RegressionPackRefresher().refresh_pack_file(
        src, dst, CommandAgentAdapter(_cmd(_GOOD_AGENT))
    )
    assert result.success is True
    assert dst.exists()
    # the refreshed pack passes run-pack
    run = RegressionPackRunner().run_pack(load_regression_pack(dst))
    assert run.success is True


# --- reports --------------------------------------------------------------


def test_refresh_report_export_and_write(tmp_path) -> None:
    _, result = RegressionPackRefresher().refresh_pack(
        _pack(), CommandAgentAdapter(_cmd(_GOOD_AGENT))
    )
    report = export_refresh_report(result)
    assert report["refreshed"] == 2
    assert report["success"] is True

    path = tmp_path / "reports" / "refresh.json"
    write_refresh_report(result, path)
    assert path.exists()
