import hashlib
import json

import pytest

from entropy_loop_core import compile_jev0_failure, import_jev0_failure
from entropy_loop_core.jev0_adapter import Jev0FailureImportError


def make_record(**overrides):
    unsigned = {
        "schema_version": 1,
        "kind": "jev0-failure",
        "action": "staged",
        "reason": "staged line budget exceeded: 10 > 1",
        "repository_fingerprint": "a" * 64,
        "head_sha": "b" * 40,
        "policy_sha256": None,
        "raw_diff_captured": False,
    }
    unsigned.update(overrides)
    payload = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return {
        **unsigned,
        "failure_id": hashlib.sha256(payload).hexdigest(),
    }


def test_import_jev0_failure_preserves_contract_boundary():
    trace = import_jev0_failure(make_record())
    assert trace.task.instruction == "jev0 blocked staged"
    assert trace.task.metadata["source"] == "jev0-failure/v1"
    assert trace.output.content == ""
    assert trace.output.metadata["raw_diff_captured"] is False
    assert trace.verification_result.rule_name == "jev0:staged"
    assert trace.verification_result.passed is False


def test_compile_jev0_failure_produces_stable_regression_case():
    case = compile_jev0_failure(make_record())
    assert case.instruction == "jev0 blocked staged"
    assert case.expected_rule == "jev0:staged"
    assert case.failure_reason == "staged line budget exceeded: 10 > 1"
    assert case.category == "unknown"
    assert case.name.startswith("regression_jev0_blocked_staged_")


def test_import_rejects_digest_tampering():
    record = make_record()
    record["reason"] = "tampered"
    with pytest.raises(Jev0FailureImportError, match="digest mismatch"):
        import_jev0_failure(record)


def test_import_rejects_raw_diff_capture():
    record = make_record(raw_diff_captured=True)
    with pytest.raises(Jev0FailureImportError, match="must not contain raw diff"):
        import_jev0_failure(record)


def test_import_rejects_schema_drift():
    record = make_record()
    record["unexpected"] = True
    with pytest.raises(Jev0FailureImportError, match="keys mismatch"):
        import_jev0_failure(record)


def test_import_does_not_invent_original_prompt_or_output():
    trace = import_jev0_failure(make_record())
    serialized = trace.model_dump_json()
    assert "original prompt" not in serialized.lower()
    assert "diff" not in trace.output.content.lower()


def test_import_accepts_supervise_action():
    trace = import_jev0_failure(make_record(action="supervise"))
    assert trace.task.instruction == "jev0 blocked supervise"
    assert trace.verification_result.rule_name == "jev0:supervise"
