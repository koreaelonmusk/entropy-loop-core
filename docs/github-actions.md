# Running a regression pack in GitHub Actions

Commit a [regression pack](regression-packs.md) to your repo, then run it in CI
so a reappearing agent regression fails the build. `entropy-loop run-pack` exits
non-zero when a known failure comes back.

This is documentation for **users** of Entropy Loop Core — this repository does
not require the example pack in its own CI.

## Minimal workflow

```yaml
name: Entropy Loop Regression Pack

on:
  pull_request:
  push:
    branches: [main]

jobs:
  entropy-loop:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Entropy Loop Core
        run: |
          python -m pip install --upgrade pip
          python -m pip install entropy-loop-core

      - name: Run regression pack
        run: |
          entropy-loop run-pack examples/json_agent_guard.pack.json \
            --json-report reports/entropy-loop.json \
            --junit-report reports/entropy-loop.junit.xml
```

## Exit codes

The `Run regression pack` step fails the job automatically when `run-pack`
returns a non-zero exit code:

| Code | Meaning |
|---|---|
| `0` | all cases passed — the job succeeds |
| `1` | a regression reappeared — the job fails |
| `2` | invalid path or malformed pack — the job fails |

## Live agent gate with refresh-pack

`refresh-pack` runs an explicit local agent command to refresh candidate outputs
before `run-pack` checks them:

```yaml
      - name: Refresh regression pack from current agent
        run: |
          entropy-loop refresh-pack examples/json_agent_guard.pack.json /tmp/refreshed.pack.json \
            -- python3 examples/json_agent_agent.py

      - name: Run refreshed regression pack
        run: |
          entropy-loop run-pack /tmp/refreshed.pack.json \
            --json-report reports/entropy-loop.json \
            --junit-report reports/entropy-loop.junit.xml
```

Boundary:

- Entropy Loop Core does not call a live agent unless you explicitly pass a
  command after `--`.
- The command is local and user-provided; no shell is used by default.
- Entropy Loop Core does not inject secrets and makes no network calls itself.

See [agent-adapters.md](agent-adapters.md) for the full behavior and exit codes.

## Static vs. live gate

Without `refresh-pack`, `run-pack` verifies the candidate outputs **stored in the
pack** — a committed snapshot. Add a `refresh-pack` step first (above) to gate on
your agent's *current* behavior.

## Compare current results against a baseline

Use `compare-reports` when you want CI to fail only on newly introduced agent
regressions, and to attach a reviewable diff of what changed.

```yaml
      - name: Run current regression pack
        run: |
          mkdir -p reports
          entropy-loop run-pack /tmp/refreshed.pack.json \
            --json-report reports/current.json || true

      - name: Compare against baseline
        run: |
          entropy-loop compare-reports baselines/entropy-loop.json reports/current.json \
            --markdown-report reports/triage.md \
            --json-report reports/triage.json \
            --fail-on new-failures
```

Notes:

- `run-pack` may exit `1` when failures exist, so CI examples may use `|| true`
  before triage; `compare-reports` then decides whether the build should fail.
- `--fail-on new-failures` (default) fails only on cases that passed in the
  baseline and fail now; `any-failures` fails on any current failure; `never`
  only reports.
- Entropy Loop Core does not upload artifacts or comment on PRs. Reports are
  local files unless your CI uploads them explicitly.
- The baseline is a plain JSON report you commit and review like any fixture.

See [regression-triage.md](regression-triage.md) for the full transition model
and exit codes.

## Use the first-party GitHub Action

The Action installs `entropy-loop-core`, compares the reports, writes a local CI
evidence bundle, and appends a step summary — no GitHub API, no token.

```yaml
name: Entropy Loop

on:
  pull_request:
  push:

jobs:
  entropy-loop:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run current regression pack
        run: |
          mkdir -p reports
          entropy-loop run-pack /tmp/refreshed.pack.json \
            --json-report reports/current.json || true

      - name: Compare reports
        uses: koreaelonmusk/entropy-loop-core@v0.8.0
        with:
          baseline-report: baselines/entropy-loop.json
          current-report: reports/current.json
          fail-on: new-failures
          evidence-dir: reports/entropy-loop-evidence
          junit-report: reports/entropy-loop-junit.xml
          write-step-summary: true

      - name: Upload Entropy Loop evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: entropy-loop-evidence
          path: reports/entropy-loop-evidence
```

Notes:

- The Action does not call the GitHub API, comment on PRs, or require
  `GITHUB_TOKEN`.
- The Action does not upload artifacts by itself — add `actions/upload-artifact`
  explicitly if you want them.
- The optional `junit-report` input writes a deterministic JUnit XML file that
  test reporters can consume; leave it empty to skip it.
- `run-pack` may exit `1` when failures exist, so CI examples may use `|| true`
  before the Action; `write-ci-evidence` then decides whether the job fails,
  based on `fail-on`.

When the Action is pinned to a semver tag such as `v0.8.0` and `package-version`
is not set, the Action installs the matching PyPI package version, for example
`entropy-loop-core==0.8.0`.

When the Action is used from a branch ref such as `main`, and `package-version`
is not set, the Action installs the latest published package from PyPI.

For fully reproducible CI on branch refs, set `package-version` explicitly.

Local CLI equivalent:

```bash
entropy-loop write-ci-evidence baselines/entropy-loop.json reports/current.json \
  --fail-on new-failures \
  --evidence-dir reports/entropy-loop-evidence \
  --append-github-step-summary
```

See [ci-evidence.md](ci-evidence.md) for the bundle contents and the step-summary
behavior.

## Notes

- Keep it minimal; add JUnit/JSON report steps only if your CI consumes them.
- The pack is a plain JSON file — review it in pull requests like any other test
  fixture.
- Skipped cases (no stored output) do not fail the build.
- No secrets, tokens, or network access are required to run a pack.
