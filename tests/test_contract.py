"""Tests for the deterministic v1 stability contract."""

from __future__ import annotations

import json

from entropy_loop_core import (
    export_stability_contract,
    export_stability_contract_json,
    write_stability_contract_json,
)


def test_contract_has_core_identity() -> None:
    c = export_stability_contract()
    assert c["project"] == "entropy-loop-core"
    assert c["contract_version"] == "1"
    assert c["package_version"]  # non-empty


def test_contract_json_parses() -> None:
    data = json.loads(export_stability_contract_json())
    assert data["project"] == "entropy-loop-core"


def test_contract_is_deterministic() -> None:
    assert export_stability_contract_json() == export_stability_contract_json()


def test_contract_json_has_sorted_keys() -> None:
    text = export_stability_contract_json()
    data = json.loads(text)
    # Re-dump with sorted keys must equal the exporter output.
    assert json.dumps(data, indent=2, sort_keys=True) + "\n" == text


def test_contract_exit_codes() -> None:
    codes = export_stability_contract()["stable_surfaces"]["cli_exit_codes"]
    assert codes["success"] == 0
    assert codes["policy_failure"] == 1
    assert codes["usage_or_write_error"] == 2


def test_contract_bundle_files_exact() -> None:
    files = export_stability_contract()["stable_surfaces"]["ci_evidence_bundle_files"]
    assert files == ["manifest.json", "summary.txt", "triage.json", "triage.md"]


def test_contract_report_outputs_include_html() -> None:
    outputs = export_stability_contract()["stable_surfaces"]["report_outputs"]
    assert "html" in outputs
    assert "junit_xml" in outputs


def test_contract_has_junit_semantics() -> None:
    statement = export_stability_contract()["junit_semantics"]["statement"]
    assert statement == (
        "JUnit failures indicate reported regression/test state; "
        "the selected fail-on policy controls the process exit code."
    )


def test_contract_action_boundary() -> None:
    action = export_stability_contract()["github_action"]
    assert "html-report" in action["inputs"]
    assert "junit-report" in action["inputs"]
    joined = " ".join(action["boundary"]).lower()
    assert "no github api" in joined
    assert "github_token" in joined.lower() or "token" in joined


def test_contract_contains_cli_commands() -> None:
    commands = export_stability_contract()["cli_commands"]
    for name in ("contract", "compare-reports", "write-ci-evidence", "ci-demo"):
        assert name in commands


def test_contract_no_timestamps_or_abs_paths() -> None:
    text = export_stability_contract_json()
    assert "2026" not in text
    assert "/Users/" not in text
    assert "/home/" not in text


def test_contract_writer_matches_exporter(tmp_path) -> None:
    path = tmp_path / "out" / "contract.json"
    write_stability_contract_json(path)
    assert path.exists()
    assert path.read_text() == export_stability_contract_json()
