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

## v0.3.0 — Replay (current)

Theme: *failures should not only be remembered — they should be replayed.*
Generated regression cases become a runnable suite so a remembered failure can be
re-checked, not just stored. Shipped: `RegressionSuite`, `RegressionRunner`,
`RegressionRunResult`, `RegressionReport`, suite import/export and JSON
save/load, and `entropy-loop replay-demo`.

## v0.4.0 — Memory policy

Decide what to remember, group, and forget. `MemoryPolicy`, `LessonCompactor`,
`LessonMemory`, `CompactionResult`, memory import/export, and
`entropy-loop memory-demo` — deterministic lesson deduplication (by fingerprint
or category), minimum-occurrence and count caps, and drop-empty hygiene.

## v0.5.0 — Regression pack + CI gate (in progress)

Turn agent failures into portable CI checks. `RegressionPack`,
`RegressionPackRunner`, JSON/JUnit reports, and `entropy-loop run-pack` with
stable exit codes (0/1/2) so a reappearing regression fails the build. No version
bump until a release is cut.

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
