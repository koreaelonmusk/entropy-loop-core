# Regression triage and baseline diff

`run-pack` tells you *whether* a regression run passed. Regression triage tells
you *what changed* since a baseline run — which cases newly fail, which got
fixed, which were already failing, and which are missing. It turns a red CI run
into a reviewable diff.

> Don't just fail CI. Explain what changed.

Everything here is deterministic and local: it compares two JSON report files (or
two dicts), classifies each case's movement, and writes a JSON or Markdown
report. No LLM calls, no network, no GitHub API, no telemetry, no hidden
persistence, and no root-cause analysis — only an honest diff of two reports.

## What `compare-reports` compares

The input is two reports produced by `run-pack --json-report`:

- a **baseline** report — a known-good (or known) snapshot you keep in the repo,
- a **current** report — the run you just produced in CI.

Each report carries a `case_results` list (added in v0.7.0) of
`{case, status, message}` entries. Triage joins the two lists by case id and
classifies each case.

## Transition classification

For every case seen in either report, triage assigns one transition:

| transition            | baseline → current      | meaning                          |
| --------------------- | ----------------------- | -------------------------------- |
| `new_failure`         | passed → failed         | newly broken                     |
| `fixed`               | failed → passed         | newly fixed                      |
| `persistent_failure`  | failed → failed         | still failing                    |
| `persistent_pass`     | passed → passed         | still passing                    |
| `new_skip`            | (any) → skipped         | now skipped                      |
| `still_skipped`       | skipped → skipped       | still skipped                    |
| `missing_in_current`  | present → absent        | dropped from the current run     |
| `new_case`            | absent → present        | added since the baseline         |
| `changed` / `unknown` | anything else           | a change that isn't one of above |

Ordering is stable (by case id) and summaries are deterministic, so the same two
reports always produce byte-identical output.

## `--fail-on` policy

`compare-reports` decides the build outcome with a small policy:

- `new-failures` (default) — exit `1` only when a case that passed in the
  baseline now fails. Persistent failures are **reported but do not fail the
  build**, so a long-standing known failure doesn't block unrelated work.
- `any-failures` — exit `1` if the current report has any failing case, new or
  persistent.
- `never` — always exit `0` (given valid inputs). Useful for a report-only step.

Exit codes: `0` policy passes, `1` policy fails, `2` bad input (missing file,
invalid JSON, or invalid policy).

## Why `run-pack || true` before triage

`run-pack` exits `1` when the current run has failures, which would stop a CI job
before triage runs. Letting the run-pack step continue (`|| true`) lets you
produce the current report first, then let `compare-reports` decide whether the
build should actually fail:

```bash
entropy-loop run-pack /tmp/refreshed.pack.json --json-report reports/current.json || true
entropy-loop compare-reports baselines/entropy-loop.json reports/current.json \
  --markdown-report reports/triage.md \
  --fail-on new-failures
```

## Output

`--json-report` writes a machine-readable triage (counts + every transition).
`--markdown-report` writes a human-readable report with a summary, counts, and
sections for newly failing, fixed, persistent failures, and skipped/missing
cases. See [`examples/triage_report.md`](../examples/triage_report.md).

## CLI

```bash
entropy-loop triage-demo   # compare a baseline run to a current run, in-process
entropy-loop compare-reports baseline.json current.json \
  --markdown-report reports/triage.md \
  --json-report reports/triage.json \
  --fail-on new-failures
```

## Boundary

- Local files only; explicit paths only — no hidden baseline location, no
  auto-discovery.
- No network calls, no GitHub API, no PR comments, no artifact uploads.
- No telemetry, no hidden persistence.
- No root-cause analysis and no correctness guarantee — triage classifies
  transitions between two reports, nothing more.
- Older/minimal reports without `case_results` still compare at the aggregate
  level, but produce no per-case transitions; this limitation is reported, not
  hidden.

See also [regression-packs.md](regression-packs.md),
[agent-adapters.md](agent-adapters.md), and
[github-actions.md](github-actions.md).
