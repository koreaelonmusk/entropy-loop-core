# HTML report — the Pixel Failure Console

JUnit is for machines; the **Pixel Failure Console** is for humans. It renders a
regression triage as a single self-contained HTML file a person can open and
understand at a glance: summary cards, the policy result, and sections for new,
persistent, resolved, and skipped/missing cases.

It is deterministic and fully self-contained — inline CSS only, **no external
stylesheets, scripts, fonts, images, or network requests** — so it opens offline
and renders identically everywhere. No timestamps, no hostnames, standard library
only.

## Write one

```bash
entropy-loop compare-reports baselines/entropy-loop.json reports/current.json \
  --fail-on new-failures \
  --html-report reports/entropy-loop.html
```

`write-ci-evidence` accepts `--html-report` too, and it combines with
`--json-report`, `--markdown-report`, and `--junit-report`. The GitHub Action
exposes an optional `html-report` input mapping to the same flag (empty means no
HTML file). `--html-report` writes an extra file; it does **not** change the
default 4-file evidence bundle. An invalid output path exits `2`.

From Python:

```python
from entropy_loop_core import write_regression_triage_html
write_regression_triage_html(triage, "reports/entropy-loop.html")
```

## What's in it

- Title **Entropy Loop Failure Console** and subtitle
  **AI agent regressions as CI evidence**.
- Package/version and policy line.
- Summary cards: total cases, new failures, persistent failures, resolved,
  skipped/missing.
- The policy result (PASS / FAIL) and this note:

  > JUnit failures indicate reported regression/test state; the selected fail-on
  > policy controls the process exit code.

- Sections: New Failures, Persistent Failures, Resolved Cases,
  Skipped / Missing Cases, Evidence Files, and a suggested CI command.
- A boundary footer.

## Design

A tasteful, terminal-style, pixel-art inspired dark theme built purely from CSS
(pixel accent strip, blocky cards, monospace). It reads fine without JavaScript,
prints reasonably, and keeps accessible contrast. HTML is escaped, ordering is
stable, and output is byte-identical across runs on the same input.

## Boundary

- Deterministic local file; inline assets only; no network, no CDN, no JS
  dependency, no telemetry.
- Not root-cause analysis and no correctness guarantee — it reports transition
  state, nothing more.
