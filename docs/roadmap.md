# Roadmap

Entropy Loop Core aims to stay small and dependable while sharpening one idea:
compiling agent failures into reusable assets. This roadmap is conservative and
directional, not a commitment. It contains no private commercial detail.

## v0.1.0 — Failure Compiler foundations (current)

- Typed data contract: `Task`, `AgentOutput`, `VerificationResult`,
  `FailureTrace`, `Lesson`, `RetryContext`, `LoopResult`, `RegressionCase`.
- In-memory `MemoryStore` with failure history and relevant-lesson recall.
- Deterministic, fluent `Verifier` (`require_non_empty`, `require_terms`,
  `expect_json`, `max_length`).
- Deterministic `LessonGenerator` (no LLM, no network).
- `generate_regression_case` for test-like cases from failures.
- `EntropyLoop` orchestrating verify → trace → learn → retry.
- `entropy-loop demo` CLI, a worked example, tests, and docs.

## Future (not now)

Deferred until a real, public use case justifies the added surface:

- async support,
- a custom verifier registry / pluggable rules,
- persistence adapters (file, then others),
- evaluation reports,
- framework integrations,
- advanced memory and reliability policies.

## Non-goals

- Proprietary or vendor-specific agent logic.
- LLM or network calls inside the core.
- Databases, vector stores, or embeddings in the core.
- Heavyweight orchestration, web servers, or UI frameworks.
- Private commercial roadmap details of any kind.

Commercial products may build private policies, datasets, dashboards, and
deployment workflows on top of this open-source core — those live elsewhere, not
in this repository.
