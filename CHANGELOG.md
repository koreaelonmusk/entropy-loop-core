# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-07-09

Theme: **regression pack + CI gate**. Turn captured agent failures into portable
packs that run in CI and fail the build when a known regression reappears.

### Added

- `RegressionPack` — a portable, self-contained pack (cases + verification policy
  + reference outputs) that replays deterministically without a live agent.
- `RegressionPackResult` and `RegressionPackRunner` (`run_pack`, `run_pack_file`).
- Pack import/export + local JSON save/load helpers.
- JSON and JUnit report writers (`export/write_json_report`,
  `export/write_junit_report`).
- `entropy-loop pack-demo` and `entropy-loop run-pack` (stable exit codes:
  0 pass, 1 failure, 2 bad input; optional `--json-report` / `--junit-report`).
- `examples/regression_pack_ci.py`, `examples/json_agent_guard.pack.json`,
  `docs/regression-packs.md`, and `docs/github-actions.md`.

### Safety

- Deterministic; no LLM calls, no network, no database, no vector store, no RAG,
  no telemetry, no hidden persistence.
- `run-pack` verifies stored candidate outputs from a pack; it does not call a
  live agent. Exit codes: `0` pass, `1` regression failure, `2` invalid input.

## [0.4.0] - 2026-07-09

Theme: **memory policy + lesson compaction**. Failure memory should not grow
without bound; v0.4.0 decides what to keep, merge, and drop.

### Added

- `MemoryPolicy` — a deterministic policy for retaining and compacting lessons
  (dedupe by fingerprint or category, `max_lessons`, `min_occurrences`, per-category
  caps, drop-empty, keep-latest).
- `LessonMemory` and `CompactionResult` typed models.
- `LessonCompactor` — `compact(...)` and `compact_memory(...)`, deterministic and
  side-effect free.
- Memory import/export + local JSON save/load helpers.
- `entropy-loop memory-demo` CLI command.
- `examples/memory_policy_guard.py` and `docs/memory-policy.md`.

### Safety

- Still deterministic; no LLM calls, no network, no database, no vector store.
- No hidden persistence; no private business logic; no customer data.

## [0.3.1] - 2026-07-09

Theme: **packaging readiness**. A stabilization release — no runtime behavior
changes and no new features.

### Added

- `py.typed` marker for PEP 561 typing support (shipped in the wheel).
- Packaging metadata: `Development Status :: 4 - Beta`, `Typing :: Typed`, and
  `Issues` / `Changelog` project URLs.
- `build` and `twine` as dev-only dependencies.
- `docs/release-checklist.md` and `docs/stabilization-v0.3.1.md`.
- A CI `package` job running `python -m build` and `twine check dist/*`.

### Changed

- README clarifies source install (a package-index install is planned after
  stabilization; no PyPI install command or badge yet).

### Safety

- No runtime behavior changes, no network calls, no external AI API calls.
- No private business logic, customer data, private prompts, or secrets.

## [0.3.0] - 2026-07-09

Theme: **replay**. Where v0.2.0 *generated* regression cases, v0.3.0 *replays*
them: turn failed agent outputs into regression cases and re-run them before the
same agent bug ships again.

### Added

- `RegressionSuite` — a named collection of regression cases.
- `RegressionRunner` — replays cases through an agent + verifier (`run_case`,
  `run_suite`), deterministic and no-retry.
- `RegressionRunResult` and `RegressionReport` (with a `success_rate`).
- Regression suite import/export and local JSON save/load helpers:
  `export_regression_suite`, `import_regression_suite`,
  `export_regression_report`, `save_regression_suite`, `load_regression_suite`.
- `entropy-loop replay-demo` CLI command.
- `examples/json_agent_guard.py` — capture a broken-JSON failure and replay it.

### Changed

- README leads with the practical hook: turn failed outputs into regression
  cases and replay them.
- The reliability model now covers replay.

### Safety

- Still deterministic; no network calls; no external AI API calls.
- No private business logic; no customer data.

## [0.2.0] - 2026-07-09

Theme: **failure classification + policy-based verification + reproducible
regression**. Failures are now classified, fingerprinted, and summarized — the
central loop gets sharper without getting bigger.

### Added

- Failure categories (`FailureCategory`): `empty_output`,
  `missing_required_term`, `invalid_json`, `too_long`, `agent_exception`,
  `unknown`.
- `VerificationPolicy` and `Verifier.from_policy` for declarative rule config.
- Deterministic, public-safe failure fingerprints on every `FailureTrace`.
- `EvaluationSummary` and `summarize` for run rollups.
- Regression case export: `export_regression_case` / `export_regression_cases`.
- Improved `entropy-loop demo` (category, fingerprint, summary, regression case)
  and a new `entropy-loop doctor` health-check command.
- `docs/reliability-model.md`.

### Changed

- `VerificationResult` now includes structured failure information (`category`,
  `details`).
- Lessons are generated based on public-safe failure categories.

### Safety

- No external API calls.
- No private business logic.
- No customer data.
- No enterprise features.

## [0.1.0] - 2026-07-09

Introduces the **Failure Compiler** architecture: failures are compiled into
lessons and regression cases rather than merely retried.

### Added

- Typed data contract: `Task`, `AgentOutput`, `VerificationResult`,
  `FailureTrace`, `Lesson`, `RetryContext`, `LoopResult`, `RegressionCase`, and
  the `Severity` / `Status` literals.
- `Verifier` — fluent, deterministic output validation: `require_non_empty`,
  `require_terms`, `expect_json`, and `max_length`.
- `LessonGenerator` — deterministic compilation of failure traces into reusable
  lessons (no LLM, no network).
- `generate_regression_case` — generates test-like regression cases from
  failures.
- `MemoryStore` — in-memory storage for failure traces and lessons, with
  `recent_failures`, `all_lessons`, and keyword-based `relevant_lessons` recall.
- `EntropyLoop` — run a task, verify, trace failures, compile lessons, and retry
  with a `RetryContext` carrying prior failures and lessons.
- `entropy-loop demo` CLI narrating the full compiler pipeline.
- Worked example, architecture/philosophy/roadmap/research docs, a public/private
  boundary policy, and a test suite.

[0.5.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.5.0
[0.4.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.4.0
[0.3.1]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.3.1
[0.3.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.3.0
[0.2.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.2.0
[0.1.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.1.0
