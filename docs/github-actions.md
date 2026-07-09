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

## Notes

- Keep it minimal; add JUnit/JSON report steps only if your CI consumes them.
- The pack is a plain JSON file — review it in pull requests like any other test
  fixture.
- Skipped cases (no stored output) do not fail the build.
- No secrets, tokens, or network access are required to run a pack.
