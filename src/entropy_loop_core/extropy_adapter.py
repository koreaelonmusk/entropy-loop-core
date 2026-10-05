"""Strict adapter from extropy-failure/v1 into entropy-loop-core failures.

The contract is intentionally public-safe and raw-diff-free. Extropy exports only
content-addressed execution/delta identity plus the typed failure verdict needed
to compile a deterministic regression case.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .regression import generate_regression_case
from .types import AgentOutput, FailureTrace, RegressionCase, Task, VerificationResult

EXTROPY_FAILURE_SCHEMA_VERSION = 1
EXTROPY_FAILURE_KIND = "extropy-failure"
EXTROPY_FAILURE_TYPES = {
    "SCOPE_DRIFT",
    "INCOMPLETE_EVIDENCE",
    "REVISION_MISMATCH",
}
EXTROPY_FAILURE_REQUIRED_KEYS = {
    "schema_version",
    "kind",
    "failure_type",
    "work_id",
    "run_id",
    "capability_id",
    "execution_report_sha256",
    "entropy_delta_sha256",
    "source_revision",
    "unexpected_path_count",
    "raw_diff_captured",
    "failure_id",
}


class ExtropyFailureImportError(ValueError):
    """Raised when an extropy-failure/v1 envelope is invalid or unsupported."""


def _sha256_json(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_lower_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def validate_extropy_failure(record: Any) -> dict[str, Any]:
    """Validate one strict, raw-diff-free extropy-failure/v1 envelope."""
    if not isinstance(record, dict) or set(record) != EXTROPY_FAILURE_REQUIRED_KEYS:
        raise ExtropyFailureImportError("extropy failure keys mismatch")
    if record["schema_version"] != EXTROPY_FAILURE_SCHEMA_VERSION:
        raise ExtropyFailureImportError("unsupported extropy failure schema_version")
    if record["kind"] != EXTROPY_FAILURE_KIND:
        raise ExtropyFailureImportError("invalid extropy failure kind")
    if record["failure_type"] not in EXTROPY_FAILURE_TYPES:
        raise ExtropyFailureImportError("unsupported extropy failure type")

    for key in ("work_id", "run_id", "capability_id"):
        if not isinstance(record[key], str) or not record[key].strip():
            raise ExtropyFailureImportError(f"{key} must be a non-empty string")
        if "\n" in record[key] or "\r" in record[key]:
            raise ExtropyFailureImportError(f"{key} must be one line")

    for key in ("execution_report_sha256", "entropy_delta_sha256"):
        if not _is_lower_sha256(record[key]):
            raise ExtropyFailureImportError(f"{key} must be lowercase SHA-256")

    revision = record["source_revision"]
    if (
        not isinstance(revision, str)
        or len(revision) not in (40, 64)
        or any(ch not in "0123456789abcdef" for ch in revision)
    ):
        raise ExtropyFailureImportError(
            "source_revision must be a lowercase Git object id"
        )

    count = record["unexpected_path_count"]
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ExtropyFailureImportError(
            "unexpected_path_count must be a non-negative integer"
        )

    if record["raw_diff_captured"] is not False:
        raise ExtropyFailureImportError(
            "extropy-failure/v1 must not contain raw diff"
        )

    supplied = record["failure_id"]
    if not _is_lower_sha256(supplied):
        raise ExtropyFailureImportError("failure_id must be lowercase SHA-256")
    unsigned = dict(record)
    del unsigned["failure_id"]
    if supplied != _sha256_json(unsigned):
        raise ExtropyFailureImportError("extropy failure digest mismatch")
    return record


def import_extropy_failure(record: Any) -> FailureTrace:
    """Map a valid Extropy execution-evidence failure into a FailureTrace."""
    data = validate_extropy_failure(record)
    failure_type = data["failure_type"]
    source = "extropy-failure/v1"
    reason = f"Extropy post-write evidence rejected execution: {failure_type}"
    rule_name = f"extropy:entropy-delta:{failure_type}"

    task = Task(
        id=data["failure_id"],
        instruction=f"Extropy rejected post-write scope: {failure_type}",
        metadata={
            "source": source,
            "work_id": data["work_id"],
            "run_id": data["run_id"],
            "capability_id": data["capability_id"],
            "execution_report_sha256": data["execution_report_sha256"],
            "entropy_delta_sha256": data["entropy_delta_sha256"],
            "source_revision": data["source_revision"],
            "unexpected_path_count": data["unexpected_path_count"],
        },
    )
    output = AgentOutput(
        content="",
        metadata={
            "source": source,
            "raw_diff_captured": False,
        },
    )
    verification = VerificationResult(
        passed=False,
        reason=reason,
        rule_name=rule_name,
        severity="error",
        category="unknown",
        details={
            "failure_id": data["failure_id"],
            "failure_type": failure_type,
        },
    )
    return FailureTrace(
        task=task,
        output=output,
        verification_result=verification,
        attempt=1,
    )


def compile_extropy_failure(record: Any) -> RegressionCase:
    """Compile one valid Extropy failure directly into a regression case."""
    return generate_regression_case(import_extropy_failure(record))
