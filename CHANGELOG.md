# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.1.0
