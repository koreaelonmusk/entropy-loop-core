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

## Static vs. live gate

`run-pack` verifies the candidate outputs **stored in the pack** — it does not
call your agent. The workflow above therefore checks a committed snapshot.

To gate on your agent's *current* behavior, add a step **before** `run-pack` that
runs your agent and refreshes the pack's outputs (via `save_regression_pack`),
then run `run-pack` against the refreshed pack. See
[regression-packs.md](regression-packs.md#what-run-pack-checks-and-what-it-does-not).

## Notes

- Keep it minimal; add JUnit/JSON report steps only if your CI consumes them.
- The pack is a plain JSON file — review it in pull requests like any other test
  fixture.
- Skipped cases (no stored output) do not fail the build.
- No secrets, tokens, or network access are required to run a pack.
