"""A deterministic v1 stability contract for Entropy Loop Core.

The contract is a machine-readable declaration of the surfaces this project
promises to keep stable: the public Python exports, the CLI commands and their
exit-code meanings, the default CI evidence bundle files, the report outputs, the
GitHub Action inputs and boundary, and the JUnit semantics.

It is deterministic and local: standard library only, sorted keys, no timestamps,
no hostnames, no absolute paths, no network, and no hidden persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONTRACT_VERSION = "1"

# The exact JUnit semantics sentence, shared with the reports and docs.
JUNIT_SEMANTICS = (
    "JUnit failures indicate reported regression/test state; "
    "the selected fail-on policy controls the process exit code."
)

# The CLI commands this project promises to keep working.
_CLI_COMMANDS = (
    "agent-demo",
    "ci-demo",
    "compare-reports",
    "contract",
    "demo",
    "doctor",
    "memory-demo",
    "pack-demo",
    "refresh-pack",
    "replay-demo",
    "run-pack",
    "triage-demo",
    "write-ci-evidence",
)

# The default CI evidence bundle file names (order is part of the contract).
_EVIDENCE_BUNDLE_FILES = (
    "manifest.json",
    "summary.txt",
    "triage.json",
    "triage.md",
)

# The GitHub Action inputs.
_ACTION_INPUTS = (
    "baseline-report",
    "current-report",
    "evidence-dir",
    "fail-on",
    "html-report",
    "install-package",
    "json-report",
    "junit-report",
    "markdown-report",
    "package-version",
    "python-command",
    "write-step-summary",
)

_ACTION_BOUNDARY = (
    "no GitHub API calls",
    "no PR comments",
    "no artifact upload by default",
    "no required GITHUB_TOKEN",
    "no write permissions required",
)

_BOUNDARIES = (
    "deterministic local files only",
    "standard library only, no network calls",
    "no LLM calls",
    "no telemetry",
    "no hidden persistence",
    "no database, vector store, or RAG",
    "not root-cause analysis",
    "no guaranteed-correctness claims",
)


def export_stability_contract() -> dict[str, Any]:
    """Return the stability contract as a plain, deterministic dictionary."""
    from . import __all__, __version__

    exports = sorted(name for name in __all__ if name != "__version__")
    return {
        "project": "entropy-loop-core",
        "contract_version": _CONTRACT_VERSION,
        "package_version": __version__,
        "python_exports": exports,
        "cli_commands": sorted(_CLI_COMMANDS),
        "stable_surfaces": {
            "cli_exit_codes": {
                "success": 0,
                "policy_failure": 1,
                "usage_or_write_error": 2,
            },
            "ci_evidence_bundle_files": list(_EVIDENCE_BUNDLE_FILES),
            "report_outputs": ["json", "markdown", "junit_xml", "html"],
        },
        "github_action": {
            "inputs": sorted(_ACTION_INPUTS),
            "boundary": list(_ACTION_BOUNDARY),
        },
        "junit_semantics": {
            "statement": JUNIT_SEMANTICS,
            "notes": [
                "Persistent failures can appear as JUnit <failure> entries "
                "even when --fail-on new-failures exits 0.",
                "Missing current cases are represented as skipped testcases.",
            ],
        },
        "boundaries": list(_BOUNDARIES),
    }


def export_stability_contract_json(indent: int = 2) -> str:
    """Render the stability contract as deterministic JSON (sorted keys)."""
    return json.dumps(export_stability_contract(), indent=indent, sort_keys=True) + "\n"


def write_stability_contract_json(path: str | Path) -> None:
    """Write the stability contract JSON to ``path`` (creating parent dirs)."""
    target = Path(path)
    if target.parent != Path(""):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export_stability_contract_json(), encoding="utf-8")
