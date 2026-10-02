"""Strict adapter from jev0-failure/v1 into entropy-loop-core failures.

This module intentionally depends on the neutral JSON contract, not on jev0
Python code. That preserves jev0's zero-dependency runtime boundary.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .regression import generate_regression_case
from .types import AgentOutput, FailureTrace, RegressionCase, Task, VerificationResult

JEV0_FAILURE_SCHEMA_VERSION = 1
JEV0_FAILURE_KIND = "jev0-failure"
JEV0_FAILURE_REQUIRED_KEYS = {
    "schema_version",
    "kind",
    "action",
    "reason",
    "repository_fingerprint",
    "head_sha",
    "policy_sha256",
    "raw_diff_captured",
    "failure_id",
}


class Jev0FailureImportError(ValueError):
    """Raised when a jev0 failure envelope is invalid or unsupported."""


def _sha256_json(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_jev0_failure(record: Any) -> dict[str, Any]:
    """Validate one strict, raw-diff-free jev0-failure/v1 envelope."""
    if not isinstance(record, dict) or set(record) != JEV0_FAILURE_REQUIRED_KEYS:
        raise Jev0FailureImportError("jev0 failure keys mismatch")
    if record["schema_version"] != JEV0_FAILURE_SCHEMA_VERSION:
        raise Jev0FailureImportError("unsupported jev0 failure schema_version")
    if record["kind"] != JEV0_FAILURE_KIND:
        raise Jev0FailureImportError("invalid jev0 failure kind")
    if record["action"] not in {"staged", "workspace", "range", "run"}:
        raise Jev0FailureImportError("unsupported jev0 failure action")
    if not isinstance(record["reason"], str) or not record["reason"]:
        raise Jev0FailureImportError("jev0 failure reason must be non-empty")
    if "
" in record["reason"] or "" in record["reason"]:
        raise Jev0FailureImportError("jev0 failure reason must be one line")
    if not isinstance(record["repository_fingerprint"], str):
        raise Jev0FailureImportError("repository_fingerprint must be a string")
    if len(record["repository_fingerprint"]) != 64:
        raise Jev0FailureImportError("repository_fingerprint must be SHA-256")
    if any(ch not in "0123456789abcdef" for ch in record["repository_fingerprint"]):
        raise Jev0FailureImportError("repository_fingerprint must be lowercase hex")
    for key in ("policy_sha256",):
        value = record[key]
        if value is not None and (
            not isinstance(value, str)
            or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)
        ):
            raise Jev0FailureImportError(f"{key} must be null or SHA-256")
    head = record["head_sha"]
    if head is not None and (
        not isinstance(head, str)
        or len(head) not in (40, 64)
        or any(ch not in "0123456789abcdef" for ch in head)
    ):
        raise Jev0FailureImportError("head_sha must be null or a Git object id")
    if record["raw_diff_captured"] is not False:
        raise Jev0FailureImportError("jev0-failure/v1 must not contain raw diff")

    supplied = record["failure_id"]
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(ch not in "0123456789abcdef" for ch in supplied)
    ):
        raise Jev0FailureImportError("failure_id must be lowercase SHA-256")
    unsigned = dict(record)
    del unsigned["failure_id"]
    if supplied != _sha256_json(unsigned):
        raise Jev0FailureImportError("jev0 failure digest mismatch")
    return record


def import_jev0_failure(record: Any) -> FailureTrace:
    """Map a valid jev0 failure envelope into a FailureTrace.

    jev0 does not capture the originating user prompt in v1, so this adapter does
    not invent it. The task instruction records only the deterministic guard
    event while source identity remains in metadata.
    """
    data = validate_jev0_failure(record)
    action = data["action"]
    task = Task(
        id=data["failure_id"],
        instruction=f"jev0 blocked {action}",
        metadata={
            "source": "jev0-failure/v1",
            "repository_fingerprint": data["repository_fingerprint"],
            "head_sha": data["head_sha"],
            "policy_sha256": data["policy_sha256"],
        },
    )
    output = AgentOutput(
        content="",
        metadata={
            "source": "jev0-failure/v1",
            "raw_diff_captured": False,
        },
    )
    verification = VerificationResult(
        passed=False,
        reason=data["reason"],
        rule_name=f"jev0:{action}",
        severity="error",
        category="unknown",
        details={"failure_id": data["failure_id"]},
    )
    return FailureTrace(
        task=task,
        output=output,
        verification_result=verification,
        attempt=1,
    )


def compile_jev0_failure(record: Any) -> RegressionCase:
    """Compile one valid jev0 failure directly into a regression case."""
    return generate_regression_case(import_jev0_failure(record))
