import hashlib
import json

import pytest

from entropy_loop_core import compile_extropy_failure, import_extropy_failure
from entropy_loop_core.extropy_adapter import ExtropyFailureImportError


def make_record(**overrides):
    unsigned = {
        "schema_version": 1,
        "kind": "extropy-failure",
        "failure_type": "SCOPE_DRIFT",
        "work_id": "work:1",
        "run_id": "run:1",
        "capability_id": "tool/mcp/extropy-local/write_file",
        "execution_report_sha256": "a" * 64,
        "entropy_delta_sha256": "b" * 64,
        "source_revision": "c" * 40,
        "unexpected_path_count": 1,
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


def test_import_extropy_failure_preserves_public_safe_boundary():
    trace = import_extropy_failure(make_record())
    assert trace.task.instruction == "Extropy rejected post-write scope: SCOPE_DRIFT"
    assert trace.task.metadata["source"] == "extropy-failure/v1"
    assert trace.task.metadata["unexpected_path_count"] == 1
    assert trace.output.content == ""
    assert trace.output.metadata["raw_diff_captured"] is False
    assert trace.verification_result.rule_name == "extropy:entropy-delta:SCOPE_DRIFT"
    assert trace.verification_result.passed is False


def test_compile_extropy_failure_produces_stable_regression_case():
    case = compile_extropy_failure(make_record())
    assert case.expected_rule == "extropy:entropy-delta:SCOPE_DRIFT"
    assert case.failure_reason == "Extropy post-write evidence rejected execution: SCOPE_DRIFT"
    assert case.category == "unknown"
    assert case.name.startswith("regression_extropy_rejected_post_write_scope")


@pytest.mark.parametrize(
    "failure_type",
    ["SCOPE_DRIFT", "INCOMPLETE_EVIDENCE", "REVISION_MISMATCH"],
)
def test_import_accepts_supported_entropy_failure_types(failure_type):
    trace = import_extropy_failure(make_record(failure_type=failure_type))
    assert trace.verification_result.rule_name == f"extropy:entropy-delta:{failure_type}"


def test_import_rejects_digest_tampering():
    record = make_record()
    record["unexpected_path_count"] = 2
    with pytest.raises(ExtropyFailureImportError, match="digest mismatch"):
        import_extropy_failure(record)


def test_import_rejects_raw_diff_capture():
    record = make_record(raw_diff_captured=True)
    with pytest.raises(ExtropyFailureImportError, match="must not contain raw diff"):
        import_extropy_failure(record)


def test_import_rejects_schema_drift():
    record = make_record()
    record["unexpected_paths"] = ["secret/path.ts"]
    with pytest.raises(ExtropyFailureImportError, match="keys mismatch"):
        import_extropy_failure(record)


def test_import_rejects_non_hash_evidence_identity():
    with pytest.raises(ExtropyFailureImportError, match="entropy_delta_sha256"):
        import_extropy_failure(make_record(entropy_delta_sha256="not-a-sha"))


def test_import_does_not_invent_prompt_diff_or_path_list():
    trace = import_extropy_failure(make_record())
    serialized = trace.model_dump_json().lower()
    assert "original prompt" not in serialized
    assert "unexpected_paths" not in serialized
    assert "raw diff" not in trace.output.content.lower()
