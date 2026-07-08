# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-09

Introduces the **Failure Compiler** architecture: failures are compiled into
lessons and regression cases rather than merely retried.

### Added

- Typed data contract: `Task`, `AgentOutput`, `VerificationResult`,
  `FailureTrace`, `Lesson`, `RegressionCase`, `AgentContext`, `LoopResult`,
  `LoopStatus`, `Severity`.
- `Verifier` — rule-based output validation with composable rules:
  `non_empty_output`, `contains_required_terms`, `valid_json_when_expected`,
  and `max_length`.
- `LessonGenerator` — deterministic compilation of failure traces into reusable
  lessons (no LLM, no network).
- `RegressionGenerator` — generates test-like regression cases from failures.
- `MemoryStore` — in-memory storage for failure traces and lessons, with
  `recent_failures` and keyword-based `relevant_lessons` recall.
- `EntropyLoop` — run a task, verify, trace failures, compile lessons, retry
  with lessons in context, and optionally generate regression cases.
- `entropy-loop demo` CLI narrating the full compiler pipeline.
- Worked example, architecture/philosophy/roadmap docs, and a test suite.

[0.1.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.1.0
