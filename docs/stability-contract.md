# Stability contract

The stability contract is a machine-readable declaration of the surfaces Entropy
Loop Core promises to keep stable. It lets a team see, in one JSON file, exactly
what they are depending on — the public Python exports, the CLI commands and
their exit-code meanings, the default CI evidence bundle files, the report
outputs, the GitHub Action inputs and boundary, and the JUnit semantics.

It is deterministic and local: standard library only, sorted keys, no timestamps,
no hostnames, no absolute paths, no network, and no hidden persistence. The same
package version always produces byte-identical output.

## Print or write it

```bash
entropy-loop contract                                   # prints JSON to stdout
entropy-loop contract --output /tmp/entropy-loop-contract.json
```

Exit codes: `0` printed/written, `2` write error.

Or from Python:

```python
from entropy_loop_core import export_stability_contract

contract = export_stability_contract()
print(contract["stable_surfaces"]["cli_exit_codes"])
```

## What it declares

- `project`, `contract_version` (`"1"`), and `package_version`.
- `python_exports` — the sorted public API names.
- `cli_commands` — the CLI commands kept working.
- `stable_surfaces`:
  - `cli_exit_codes` — `success: 0`, `policy_failure: 1`,
    `usage_or_write_error: 2`.
  - `ci_evidence_bundle_files` — exactly `manifest.json`, `summary.txt`,
    `triage.json`, `triage.md`.
  - `report_outputs` — `json`, `markdown`, `junit_xml`, `html`.
- `github_action` — the Action `inputs` and its `boundary` (no GitHub API, no
  PR comments, no artifact upload by default, no required `GITHUB_TOKEN`).
- `junit_semantics` — including this exact statement:

  > JUnit failures indicate reported regression/test state; the selected fail-on
  > policy controls the process exit code.

- `boundaries` — the project's deterministic, local-only promises.

## Boundary

- Deterministic local JSON only — no network, no telemetry, no hidden
  persistence.
- Not root-cause analysis and no correctness guarantee — the contract declares
  surfaces, it does not evaluate your agent.
