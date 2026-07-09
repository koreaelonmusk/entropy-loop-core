"""Tests for regression packs and the CI gate."""

from __future__ import annotations

import json

import pytest

from entropy_loop_core import (
    RegressionCase,
    RegressionPack,
    RegressionPackResult,
    RegressionPackRunner,
    VerificationPolicy,
    export_json_report,
    export_junit_report,
    export_regression_pack,
    import_regression_pack,
    load_regression_pack,
    save_regression_pack,
    write_json_report,
    write_junit_report,
)


def _case(name: str) -> RegressionCase:
    return RegressionCase(
        name=name,
        instruction=f"return {name} as JSON",
        expected_rule="valid_json_when_expected",
        failure_reason="expected valid JSON",
        category="invalid_json",
    )


def _pack(outputs: dict[str, str] | None = None) -> RegressionPack:
    return RegressionPack(
        name="json-agent-guard",
        policy=VerificationPolicy(require_non_empty=True, expect_json=True),
        cases=[_case("a"), _case("b")],
        outputs=outputs if outputs is not None else {"a": "{}", "b": '{"ok": true}'},
    )


# --- RegressionPack -------------------------------------------------------


def test_pack_defaults() -> None:
    pack = _pack()
    assert pack.schema_version == "1"
    assert pack.version == "1"
    assert pack.created_by == "entropy-loop-core"
    assert len(pack.cases) == 2


def test_pack_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        RegressionPack(name="")


def test_pack_rejects_unknown_schema_version() -> None:
    with pytest.raises(ValueError):
        RegressionPack(name="p", schema_version="2")


def test_pack_metadata_preserved() -> None:
    pack = RegressionPack(name="p", metadata={"origin": "test"})
    assert pack.metadata["origin"] == "test"


# --- serialization --------------------------------------------------------


def test_pack_export_import_roundtrip() -> None:
    pack = _pack()
    assert import_regression_pack(export_regression_pack(pack)) == pack


def test_pack_save_load_roundtrip(tmp_path) -> None:
    pack = _pack()
    path = tmp_path / "pack.json"
    save_regression_pack(pack, path)
    assert path.exists()
    assert load_regression_pack(path) == pack


def test_saved_pack_has_stable_key_ordering(tmp_path) -> None:
    path = tmp_path / "pack.json"
    save_regression_pack(_pack(), path)
    text = path.read_text()
    # sort_keys=True -> top-level keys are alphabetical
    keys = list(json.loads(text).keys())
    assert keys == sorted(keys)


def test_load_malformed_json_raises(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{ not json")
    with pytest.raises(ValueError):
        load_regression_pack(path)


# --- RegressionPackRunner -------------------------------------------------


def test_run_pack_all_pass() -> None:
    result = RegressionPackRunner().run_pack(_pack())
    assert isinstance(result, RegressionPackResult)
    assert result.case_count == 2
    assert result.passed_count == 2
    assert result.failed_count == 0
    assert result.success is True
    assert "2 passed, 0 failed" in result.summary


def test_run_pack_reports_failure() -> None:
    result = RegressionPackRunner().run_pack(_pack({"a": "{}", "b": "not json"}))
    assert result.failed_count == 1
    assert result.success is False


def test_run_pack_skips_cases_without_output() -> None:
    result = RegressionPackRunner().run_pack(_pack({"a": "{}"}))
    assert result.skipped_count == 1
    assert result.passed_count == 1
    assert result.success is True


def test_run_pack_is_deterministic() -> None:
    runner = RegressionPackRunner()
    assert runner.run_pack(_pack()) == runner.run_pack(_pack())


def test_run_pack_file(tmp_path) -> None:
    path = tmp_path / "pack.json"
    save_regression_pack(_pack(), path)
    result = RegressionPackRunner().run_pack_file(path)
    assert result.success is True


# --- reports --------------------------------------------------------------


def test_json_report_contains_counts() -> None:
    result = RegressionPackRunner().run_pack(_pack())
    report = export_json_report(result)
    assert report["pack"] == "json-agent-guard"
    assert report["passed"] == 2
    assert report["success"] is True


def test_write_json_report_creates_file(tmp_path) -> None:
    result = RegressionPackRunner().run_pack(_pack())
    path = tmp_path / "reports" / "out.json"
    write_json_report(result, path)
    assert path.exists()
    assert json.loads(path.read_text())["success"] is True


def test_junit_report_is_parseable(tmp_path) -> None:
    import xml.etree.ElementTree as ET

    result = RegressionPackRunner().run_pack(_pack({"a": "{}", "b": "not json"}))
    xml = export_junit_report(result)
    root = ET.fromstring(xml)
    assert root.tag == "testsuite"
    assert root.attrib["failures"] == "1"

    path = tmp_path / "reports" / "out.xml"
    write_junit_report(result, path)
    assert path.exists()
