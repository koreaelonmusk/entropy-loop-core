import hashlib
import json

import pytest

from entropy_loop_core import (
    build_extropy_regression_artifact,
    compile_extropy_failure,
    import_extropy_failure,
    validate_extropy_regression_artifact,
)
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


def make_record_v2(**overrides):
    unsigned = {
        "schema_version": 2,
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
        "input_sha256": "d" * 64,
        "change_policy_sha256": "e" * 64,
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
    assert case.failure_reason == (
        "Extropy post-write evidence rejected execution: SCOPE_DRIFT"
    )
    assert case.category == "unknown"
    assert case.name.startswith("regression_extropy_rejected_post_write_scope")


@pytest.mark.parametrize(
    "failure_type",
    ["SCOPE_DRIFT", "INCOMPLETE_EVIDENCE", "REVISION_MISMATCH"],
)
def test_import_accepts_supported_entropy_failure_types(failure_type):
    trace = import_extropy_failure(make_record(failure_type=failure_type))
    assert trace.verification_result.rule_name == (
        f"extropy:entropy-delta:{failure_type}"
    )


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


def test_build_extropy_regression_artifact_is_content_free_and_digest_bound():
    artifact = build_extropy_regression_artifact(make_record())
    assert artifact["schema_version"] == 1
    assert artifact["kind"] == "extropy-regression-artifact"
    assert artifact["replay_kind"] == "ENTROPY_DELTA_INVARIANT"
    assert artifact["failure_type"] == "SCOPE_DRIFT"
    assert artifact["expected_rule"] == "extropy:entropy-delta:SCOPE_DRIFT"
    assert artifact["source_revision"] == "c" * 40
    assert len(artifact["artifact_id"]) == 64
    serialized = json.dumps(artifact, sort_keys=True).lower()
    assert "unexpected_paths" not in serialized
    assert "raw_diff" not in serialized
    assert "prompt" not in serialized


def test_validate_extropy_regression_artifact_rejects_tampering():
    artifact = build_extropy_regression_artifact(make_record())
    artifact["expected_rule"] = "extropy:entropy-delta:REVISION_MISMATCH"
    with pytest.raises(
        ExtropyFailureImportError,
        match="expected_rule does not match failure_type",
    ):
        validate_extropy_regression_artifact(artifact)


def test_validate_extropy_regression_artifact_rejects_schema_smuggling():
    artifact = build_extropy_regression_artifact(make_record())
    artifact["raw_diff"] = "forbidden"
    with pytest.raises(
        ExtropyFailureImportError,
        match="artifact keys mismatch",
    ):
        validate_extropy_regression_artifact(artifact)


@pytest.mark.parametrize(
    "failure_type",
    ["SCOPE_DRIFT", "INCOMPLETE_EVIDENCE", "REVISION_MISMATCH"],
)
def test_regression_artifact_supports_all_extropy_entropy_failure_types(failure_type):
    artifact = build_extropy_regression_artifact(make_record(failure_type=failure_type))
    validated = validate_extropy_regression_artifact(artifact)
    assert validated["failure_type"] == failure_type
    assert validated["expected_rule"] == f"extropy:entropy-delta:{failure_type}"


def test_v2_failure_preserves_replay_vector_without_raw_input():
    trace = import_extropy_failure(make_record_v2())
    assert trace.task.metadata["source"] == "extropy-failure/v2"
    assert trace.output.content == ""
    serialized = trace.model_dump_json().lower()
    assert "raw_diff" in serialized
    assert '"raw_diff_captured":false' in serialized
    assert "input_sha256" not in serialized
    assert "change_policy_sha256" not in serialized


def test_v2_failure_rejects_replay_vector_hash_tampering():
    record = make_record_v2()
    record["input_sha256"] = "f" * 64
    with pytest.raises(ExtropyFailureImportError, match="digest mismatch"):
        import_extropy_failure(record)


def test_v2_regression_artifact_carries_replay_vector():
    artifact = build_extropy_regression_artifact(make_record_v2())
    assert artifact["schema_version"] == 2
    assert artifact["input_sha256"] == "d" * 64
    assert artifact["change_policy_sha256"] == "e" * 64
    assert validate_extropy_regression_artifact(artifact) == artifact


def test_v2_regression_artifact_rejects_vector_tampering():
    artifact = build_extropy_regression_artifact(make_record_v2())
    artifact["change_policy_sha256"] = "f" * 64
    with pytest.raises(
        ExtropyFailureImportError,
        match="artifact digest mismatch",
    ):
        validate_extropy_regression_artifact(artifact)


def test_v1_failure_and_artifact_remain_compatible():
    failure = make_record()
    assert validate_extropy_failure(failure) == failure
    artifact = build_extropy_regression_artifact(failure)
    assert artifact["schema_version"] == 1
    assert "input_sha256" not in artifact
    assert "change_policy_sha256" not in artifact
    assert validate_extropy_regression_artifact(artifact) == artifact
