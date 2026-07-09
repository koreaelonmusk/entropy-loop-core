# Agent adapters and live pack refresh

A [regression pack](regression-packs.md) checks the candidate outputs stored in
it. An **agent adapter** lets you refresh those outputs from your *current* agent
before checking them — turning a static gate into a live one, in two explicit
steps:

1. `refresh-pack` — run your local agent command per case and capture fresh
   outputs into a new pack.
2. `run-pack` — verify those outputs deterministically (unchanged from v0.5.0).

## Why two steps

Keeping refresh and verify separate keeps the responsibility boundary clean:
`refresh-pack` executes and captures; `run-pack` verifies and returns an exit
code. Entropy Loop Core never runs your agent implicitly — only the command you
pass to `refresh-pack`.

## Explicit command execution

`refresh-pack` runs a command **you supply after `--`**:

```bash
entropy-loop refresh-pack input.pack.json output.pack.json -- python3 my_agent.py
```

- **No shell by default.** The command is run as an argv list, not through a
  shell, so there is no shell-injection surface.
- **No auto-discovery, no implicit execution.** Nothing runs unless you pass it.
- **Minimal environment by default.** The command receives a small, functional
  base environment (enough to find an interpreter) plus any keys you set on
  `AgentCommand.env`. The full process environment — which may hold secrets — is
  passed only if you opt in with `inherit_env=True`.
- **Timeout enforced.** Each case runs with a per-case timeout (default 30s,
  configurable via `--timeout`); a timeout is reported as a failure.

## How a case reaches the agent

For each `RegressionCase`, the adapter sends the case to the command on **stdin
as JSON** (`case_id`, `task`, `metadata`) and reads the **candidate output from
stdout**. Provide `AgentCommand.stdin_template` to send a custom stdin instead.
See [`examples/json_agent_agent.py`](../examples/json_agent_agent.py) for a
minimal agent.

## CLI

```bash
entropy-loop agent-demo   # in-process demo of refresh + run
entropy-loop refresh-pack input.pack.json output.pack.json \
  --json-report reports/refresh.json \
  --fail-fast \
  -- python3 my_agent.py
```

Exit codes for `refresh-pack`:

| Code | Meaning |
|---|---|
| `0` | every case refreshed |
| `1` | one or more agent runs failed (or timed out) |
| `2` | invalid pack, invalid path, invalid command, malformed JSON, or usage error |

Then gate the refreshed pack:

```bash
entropy-loop run-pack output.pack.json
```

## What it does not do

- No implicit or background execution; nothing runs without your command.
- No shell by default; no secret injection; no hidden environment leakage.
- No network calls from Entropy Loop Core itself. Your command may perform its
  own I/O — that is your responsibility.
- No hidden persistence and no telemetry.
- Not autonomous agent testing, self-improving AI, or guaranteed correctness.

## Determinism

The framework is deterministic given the adapter's outputs. Those outputs depend
on the command you run, so `refresh-pack` is only as deterministic as your agent;
`run-pack` remains fully deterministic.

## Explaining what changed

Once you have `run-pack` JSON reports from two runs, `compare-reports` diffs them
and classifies each case as newly failing, fixed, persistent, or missing — so CI
can fail only on new regressions. See [regression-triage.md](regression-triage.md)
and [ci-evidence.md](ci-evidence.md).
