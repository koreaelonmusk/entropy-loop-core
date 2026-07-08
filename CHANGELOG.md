# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-09

### Added

- Typed task and result objects: `Task`, `LoopResult`, `LoopStatus`,
  `Failure`, `Lesson`.
- `MemoryStore` — in-memory storage for failures and lessons.
- `Verifier` — rule-based output validation with composable rules and a
  `require_contains` builder.
- `EntropyLoop` — run a task, verify the output, record failures, and retry.
- `entropy-loop demo` CLI command showing fail-then-retry behavior.
- Example script, architecture and roadmap docs, and a test suite.

[0.1.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.1.0
