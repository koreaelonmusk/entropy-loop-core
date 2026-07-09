# Regression packs

A **regression pack** turns captured agent failures into a portable, inspectable
file you can commit to a repo and run in CI. Where a `RegressionSuite` lives in
memory during a run, a `RegressionPack` is a self-contained JSON artifact.

## Pack vs suite

- A `RegressionSuite` is an in-memory collection of `RegressionCase`s, run with a
  live agent and verifier.
- A `RegressionPack` bundles the cases **plus** everything needed to replay them
  deterministically without a live agent: a `VerificationPolicy` and a reference
  output per case. That makes it a stable file suitable for version control and
  CI.

## What is in a pack

| Field | Meaning |
|---|---|
| `name` | Non-empty pack name |
| `schema_version` | Pack schema version (currently `"1"`) |
| `version` | Caller-managed content version |
| `created_by` | Who produced the pack |
| `policy` | The `VerificationPolicy` used to check each case |
| `cases` | The `RegressionCase`s |
| `outputs` | Reference output content per case name |
| `metadata` | Optional free-form context |

## Save and load

```python
from entropy_loop_core import save_regression_pack, load_regression_pack

save_regression_pack(pack, "examples/json_agent_guard.pack.json")
pack = load_regression_pack("examples/json_agent_guard.pack.json")
```

Packs are written as JSON with stable key ordering, so diffs stay reviewable.

## Run a pack

```python
from entropy_loop_core import RegressionPackRunner

result = RegressionPackRunner().run_pack(pack)
print(result.summary)  # "Regression pack `...` completed: 3 passed, 0 failed, 0 skipped."
```

Each case with a reference output is replayed through the pack's policy (reusing
the existing `RegressionRunner`); cases without an output are skipped.

## Run a pack in CI

```bash
entropy-loop run-pack examples/json_agent_guard.pack.json
```

Exit codes:

| Code | Meaning |
|---|---|
| `0` | all cases passed |
| `1` | one or more cases failed (a regression reappeared) |
| `2` | invalid path, malformed pack, or usage error |

Machine-readable reports:

```bash
entropy-loop run-pack pack.json --json-report reports/entropy-loop.json
entropy-loop run-pack pack.json --junit-report reports/entropy-loop.junit.xml
```

- The **JSON report** carries the pack name, counts, `success`, and summary.
- The **JUnit report** is minimal, valid XML (one `<testsuite>`, one
  `<testcase>` per case) that CI systems can display.

See [github-actions.md](github-actions.md) for a workflow example, and
`entropy-loop pack-demo` / `examples/regression_pack_ci.py` for runnable code.

## What `run-pack` checks (and what it does not)

This is the most important thing to understand about a pack:

- **`run-pack` verifies the candidate outputs stored inside the pack** (`outputs`)
  against the pack's `policy`. The pack is **self-contained** — that is what lets
  `entropy-loop run-pack pack.json` run with no code, no callback, and no config.
- **`run-pack` does not call a live agent, LLM, network service, or any hidden
  runtime.** It only re-verifies the outputs already in the file.
- **To use it as a *live* CI gate**, generate or refresh the pack from your
  current agent's outputs *before* running `run-pack` — for example, a CI step
  that runs your agent, writes the new outputs into the pack (via
  `save_regression_pack`), then calls `entropy-loop run-pack`. The pack then
  checks whether your current agent still passes the known cases.
- **Skipped cases do not fail the build.** A case with no entry in `outputs` is
  counted as skipped, not failed.
- **A pack where *every* case is skipped exits `0`** (nothing ran). This is an
  intentional, documented edge case — check `skipped` in the report if you want
  to treat "nothing ran" as an error in your own workflow.
- **The JUnit report is intentionally minimal** — one `<testsuite>` and one
  `<testcase>` per case, produced with the Python standard library (no extra
  dependency).

In short: v0.5.0 does not run your agent for you. It gives you a deterministic
pack format and CI gate for checking known agent outputs.

## Boundaries

- Deterministic: the same pack always produces the same result.
- No LLM calls, no network calls, no database, no vector store, no RAG.
- No telemetry and no hidden persistence — packs and reports are written only to
  the explicit local paths you provide.

This is deterministic agent regression testing and a CI gate. It does not solve
AI reliability, prevent all regressions, or guarantee correctness.

To explain *what changed* between two runs — new failures vs. fixed vs.
persistent — diff their JSON reports with `compare-reports`. See
[regression-triage.md](regression-triage.md).
