# Roadmap

Entropy Loop Core aims to stay small and dependable. The roadmap below is
directional, not a commitment, and welcomes community input.

## v0.1.0 — Foundations (current)

- Typed task/result objects (`Task`, `LoopResult`, `Failure`, `Lesson`).
- In-memory `MemoryStore` for failures and lessons.
- Rule-based `Verifier` with composable rules.
- `EntropyLoop` with verify → remember → retry.
- Minimal `entropy-loop demo` CLI.
- Test suite and example.

## v0.2.0 — Learning from memory

- Feed remembered failures back into the agent on retry.
- Helpers to derive `Lesson`s from repeated failures.
- Configurable backoff between attempts.

## v0.3.0 — Pluggable persistence

- Storage interface with a file-backed and SQLite implementation.
- Optional async loop variant.

## Later

- Structured tracing/metrics hooks for observability.
- Richer built-in rule library (JSON schema, regex, length bounds).
- Adapters for popular agent frameworks.

## Non-goals

- Proprietary or vendor-specific agent logic.
- Heavyweight orchestration or workflow engines.
- Anything that compromises the small, readable core.
