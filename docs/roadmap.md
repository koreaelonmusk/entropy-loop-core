# Roadmap

Entropy Loop Core aims to stay small and dependable while sharpening one idea:
compiling agent failures into reusable assets. The roadmap below is directional,
not a commitment, and welcomes community input.

## v0.1.0 — Failure Compiler foundations (current)

- Typed data contract: `Task`, `AgentOutput`, `VerificationResult`,
  `FailureTrace`, `Lesson`, `RegressionCase`, `AgentContext`, `LoopResult`.
- Rule-based `Verifier` with `non_empty_output`, `contains_required_terms`,
  `valid_json_when_expected`, and `max_length`.
- Deterministic `LessonGenerator` (no LLM, no network).
- `RegressionGenerator` for test-like cases from failures.
- `MemoryStore` with failure history and relevant-lesson recall.
- `EntropyLoop` orchestrating verify → trace → learn → retry.
- `entropy-loop demo` CLI, worked example, tests, and docs.

## v0.2.0 — Sharper compilation

- Richer lesson synthesis from *repeated* failures, not just single traces.
- Prompt-patch application helpers so lessons fold into agent input directly.
- Configurable backoff between attempts.

## v0.3.0 — Regression as a first-class workflow

- Export `RegressionCase`s to runnable `pytest` suites.
- Replay a stored regression corpus against an agent.
- Pluggable persistence for traces and lessons (file, SQLite).

## Later

- Structured tracing/metrics hooks for observability.
- Larger built-in rule library (JSON schema, regex, numeric bounds).
- Adapters for popular agent frameworks.

## Non-goals

- Proprietary or vendor-specific agent logic.
- LLM or network calls inside the core.
- Heavyweight orchestration or workflow engines.
- Anything that compromises the small, readable, deterministic core.
