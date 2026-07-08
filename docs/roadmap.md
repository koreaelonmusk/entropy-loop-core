# Roadmap

Entropy Loop Core aims to stay small and dependable while sharpening one idea:
compiling agent failures into reusable assets. This roadmap is conservative and
directional, not a commitment. It contains no private commercial detail.

## v0.1.0 — Failure Compiler foundations

- Typed data contract: `Task`, `AgentOutput`, `VerificationResult`,
  `FailureTrace`, `Lesson`, `RetryContext`, `LoopResult`, `RegressionCase`.
- In-memory `MemoryStore` with failure history and relevant-lesson recall.
- Deterministic, fluent `Verifier`.
- Deterministic `LessonGenerator` (no LLM, no network).
- `generate_regression_case` for test-like cases from failures.
- `EntropyLoop` orchestrating verify → trace → learn → retry.
- `entropy-loop demo` CLI, a worked example, tests, and docs.

## v0.2.0 — Failure classification + policy + reproducible regression (current)

- `FailureCategory` and richer `VerificationResult` (`category`, `details`).
- `VerificationPolicy` + `Verifier.from_policy` — declarative rule configuration.
- Deterministic, public-safe failure `fingerprint` on every `FailureTrace`.
- Category-based `LessonGenerator`.
- `EvaluationSummary` and `summarize` for run rollups.
- Regression export (`export_regression_case` / `export_regression_cases`).
- Improved `entropy-loop demo` and a new `entropy-loop doctor`.
- `docs/reliability-model.md` and expanded docs.

## v0.3.0 — Replay (directional)

Theme: *failures should not only be remembered — they should be replayed.* Turn
generated regression cases into a runnable suite so a remembered failure can be
re-checked, not just stored. Candidate public-safe primitives: a regression
suite, a runner, a pass/fail report, and case load/export.

## v0.4.0 — Memory policy (directional)

Decide what to remember, group, and forget: lesson deduplication, fingerprint
grouping, memory compaction, and recent / relevant / frequent recall — all as a
simple, deterministic, public-safe policy interface.

## Later / not now

Deferred until a real, public use case justifies the added surface:

- async support,
- a custom verifier / rule registry,
- persistence adapters (file, then others) as a simple optional interface,
- richer evaluation reports,
- framework and CI integrations.

## Non-goals

- Proprietary or vendor-specific agent logic.
- LLM or network calls inside the core.
- Databases, vector stores, or embeddings in the core.
- Heavyweight orchestration, web servers, dashboards, or UI frameworks.
- Private commercial roadmap details of any kind.

Commercial products may build private policies, datasets, dashboards, and
deployment workflows on top of this open-source core — those live elsewhere, not
in this repository.
