# Architecture

Entropy Loop Core is a small, composable reliability layer for AI agents. It has
four moving parts and a set of shared typed objects.

## Overview

```
        ┌─────────────┐
Task ──▶ │ EntropyLoop │ ──▶ LoopResult
        └──────┬──────┘
               │ uses
     ┌─────────┼──────────┐
     ▼         ▼          ▼
 Verifier  MemoryStore   Agent
 (rules)   (failures/    (your callable)
            lessons)
```

## Components

### Types (`types.py`)

Pydantic models that form the data contract:

- `Task` — the work item (a prompt plus optional metadata).
- `Failure` — a single failed attempt (prompt, attempt number, reason).
- `Lesson` — a distilled takeaway grouped by topic.
- `LoopResult` — the structured outcome (status, attempts, output, errors).
- `LoopStatus` — `success` or `failed`.

### MemoryStore (`memory.py`)

An in-memory accumulator for `Failure` and `Lesson` records. It is intentionally
minimal so the interface (`record_failure`, `failures`, `failures_for`, …) can
later be backed by a durable store without changing callers.

### Verifier (`verification.py`)

Applies an ordered list of rules to an output string. A rule is any callable
that returns an error message on failure or `None` on success. The default rule
requires a non-empty output; `require_contains` is provided as a builder, and
callers can add their own via `add_rule`.

### EntropyLoop (`loop.py`)

The orchestrator. For each attempt it runs the agent, verifies the output, and
either returns success or records the failure to memory and retries — up to
`max_attempts`. Agent exceptions are caught and treated as failures so a single
bad attempt never crashes the loop.

## Design principles

- **Small surface area.** Every component does one thing.
- **Callables over inheritance.** Agents and rules are plain functions.
- **Typed boundaries.** Pydantic models keep inputs and outputs explicit.
- **No hidden state.** Memory is passed in, not global.
