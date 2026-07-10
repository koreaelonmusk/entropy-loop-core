# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-10

Theme: **v1.0.0 launch**. First stable release of the Failure Compiler for AI
agents. The v1 reliability surface is now declared stable under the Stability
Contract.

The v1.0.0 launch surface:

- **Stability Contract** — the deterministic v1 behavior boundary
  (`entropy-loop contract`).
- **HTML Failure Console** — a self-contained, human-readable failure report.
- **JUnit XML reporter** — CI-native regression reporting.
- **GitHub Action CI evidence** — local evidence generation with no GitHub API
  calls and no artifact upload by default.
- **Korean/English report support** — bilingual HTML console and README launch
  copy.
- **Haetae README launch surface** — the Korean guardian mascot worldview.

### Added

- Deterministic v1 stability contract manifest
  (`export_stability_contract`, `export_stability_contract_json`,
  `write_stability_contract_json`) and `entropy-loop contract`.
- Deterministic, self-contained HTML report — the Pixel Failure Console
  (`export_regression_triage_html`, `write_regression_triage_html`) with a
  tasteful pixel-art inspired dark theme and CSS-only motion.
- English (`en`) and Korean (`ko`) HTML report locales, and `--html-locale` on
  `entropy-loop compare-reports` and `entropy-loop write-ci-evidence`.
- `--html-report` on `entropy-loop compare-reports` and
  `entropy-loop write-ci-evidence`.
- Optional `html-report` and `html-locale` inputs on the GitHub Action, and
  Action self-test coverage that writes and checks both English and Korean
  reports.
- `docs/stability-contract.md`, `docs/html-report.md`, and a bilingual README
  global launch surface.

### Notes

- This is the v1.0.0 release cut. The package version is bumped from `0.9.0` to
  `1.0.0`; no core, CLI, JUnit, evidence-bundle, HTML-report, or Action behavior
  changes ship with this cut.
- The HTML report supports English and Korean output; the default locale is
  English.
- HTML reports are deterministic local files with inline CSS only — no external
  stylesheets, scripts, fonts, images, network calls, telemetry, GitHub API
  calls, or default artifact upload.
- Motion effects are CSS-only and respect `prefers-reduced-motion: reduce`; every
  section is readable with animation disabled and without JavaScript.
- The stability contract is deterministic JSON (sorted keys, no timestamps, no
  absolute paths) declaring the public exports, CLI commands and exit codes, the
  default evidence bundle files, report outputs, supported HTML locales, GitHub
  Action inputs/boundary, and JUnit semantics.
- This does not add SARIF, GitHub annotations, PR comments, GitHub API calls,
  telemetry, hidden persistence, or artifact upload by default.

## [0.9.0] - 2026-07-10

Theme: **CI-native reporter outputs**. Turn AI agent regressions into CI-native
test reports.

### Added

- Deterministic JUnit XML reporter for regression triage
  (`export_regression_triage_junit_xml`, `write_regression_triage_junit_xml`).
- `--junit-report` on `entropy-loop compare-reports` and
  `entropy-loop write-ci-evidence`.
- Optional `junit-report` input on the GitHub Action.
- Action self-test coverage that writes and parses a JUnit report.

### Notes

- JUnit XML output is intended for CI and test-reporting tools (GitHub Actions,
  GitLab CI, Jenkins, CircleCI, Buildkite, and others). It uses only the
  standard library, escapes XML, and includes no timestamps or hostnames.
- JUnit XML reports current regression/test state; the `fail-on` policy controls
  the process exit code. Persistent failures can appear as JUnit `<failure>`
  entries even when `--fail-on new-failures` exits `0`.
- Currently-failing cases map to `<failure>` (`new-failure` / `persistent-failure`);
  resolved and passing cases are passing testcases; missing-in-current cases map
  to `<skipped>`; legacy reports without per-case data fall back to a single
  `regression-summary` testcase.
- The default CI evidence bundle is unchanged; `--junit-report` writes an extra
  file, not into the bundle.
- This is deterministic report formatting, not root-cause analysis. No SARIF,
  GitHub annotations, GitHub API calls, PR comments, telemetry, or artifact
  upload by default.

## [0.8.1] - 2026-07-10

Theme: **Action runner hardening**. The Action now tests itself.

### Added

- A GitHub Actions self-test workflow (`.github/workflows/action-self-test.yml`)
  that dogfoods the first-party composite Action on GitHub-hosted runners.
- Local Action self-test coverage using `uses: ./`.
- CI policy exit-code self-test coverage for `write-ci-evidence`.

### Notes

- The self-test workflow verifies local Action execution (`uses: ./`), evidence
  bundle creation, step-summary behavior, and `write-ci-evidence` policy exit
  codes (`1`/`0`/`0`/`2`/`2`), plus a smoke test of the published `v0.8.0` Action
  that is skipped on pull requests to avoid fork and package-availability
  flakiness.
- This is Action runner hardening only. It does not change the public Python API.
- No GitHub API calls, PR comments, required `GITHUB_TOKEN`, telemetry, hidden
  persistence, or artifact upload by default.

## [0.8.0] - 2026-07-10

Theme: **GitHub Action + CI evidence bundle**. From regression reports to CI
evidence in one GitHub Action.

### Added

- `CIEvidenceBundle` and `CIEvidenceWriter` (`write_bundle`) — a deterministic,
  local evidence directory (`triage.json`, `triage.md`, `summary.txt`,
  `manifest.json`) written from a `RegressionTriage`.
- `export_github_step_summary` and `append_github_step_summary` — a compact,
  deterministic GitHub Actions step summary; reads only `GITHUB_STEP_SUMMARY`,
  and only when asked.
- `entropy-loop ci-demo` and `entropy-loop write-ci-evidence BASELINE CURRENT`
  (options `--fail-on`, `--evidence-dir`, `--json-report`, `--markdown-report`,
  `--github-step-summary`, `--append-github-step-summary`, `--no-step-summary`;
  exit codes 0/1/2).
- First-party composite GitHub Action (`action.yml`) that installs the package,
  runs `write-ci-evidence`, and appends a step summary.
- `docs/ci-evidence.md` and a GitHub Actions workflow example.

### Changed

- `RegressionTriage` now records the applied `policy` (backward-compatible,
  nullable) so evidence bundles and step summaries can report it.
- README and CI docs now include first-party GitHub Action usage.

### Notes

- The GitHub Action writes local CI evidence files and can append a compact
  Markdown summary to the GitHub Actions step summary. It does not call the
  GitHub API, comment on PRs, require `GITHUB_TOKEN`, or upload artifacts by
  itself; artifact upload remains explicit via `actions/upload-artifact`.
- Action package install: with `package-version` set it installs
  `entropy-loop-core==<package-version>`; when pinned to a semver tag such as
  `v0.8.0` with no `package-version` it installs the matching PyPI package (e.g.
  `entropy-loop-core==0.8.0`); on a branch ref such as `main` it installs the
  latest. Set `package-version` for reproducible CI on branch refs.

### Safety

- Local and deterministic: writes only the fixed bundle files inside the named
  directory; no timestamps, no environment capture.
- No GitHub API calls, no PR/issue comments, no artifact uploads, no
  `GITHUB_TOKEN`, no network, no telemetry, no hidden persistence.
- Deterministic CI evidence generation and report comparison — not root-cause
  analysis, no correctness guarantee.

## [0.7.0] - 2026-07-10

Theme: **regression triage + baseline diff**. Don't just fail CI — explain what
changed between a baseline run and the current one.

### Added

- `CaseTransition`, `RegressionTriage`, `TriagePolicy`, and
  `RegressionTriageEngine` (`compare_reports`, `compare_report_files`) — a
  deterministic, local baseline-vs-current diff of regression reports.
- Triage report helpers: `export_regression_triage`,
  `write_regression_triage_json`, `export_regression_triage_markdown`,
  `write_regression_triage_markdown`.
- `entropy-loop triage-demo` and `entropy-loop compare-reports BASELINE CURRENT`
  (options `--json-report`, `--markdown-report`, `--fail-on
  new-failures|any-failures|never`; exit codes: 0 policy passes, 1 policy fails,
  2 bad input).
- `examples/regression_triage_demo.py`, `examples/baseline_regression_report.json`,
  `examples/current_regression_report.json`, `examples/triage_report.md`, and
  `docs/regression-triage.md`.

### Changed

- `run-pack --json-report` now includes a backward-compatible `case_results`
  list (`{case, status, message}`, sorted by case name) so runs can be diffed
  case by case. Existing aggregate keys are unchanged.

### Notes

- Reports generated by v0.6.0 or older may not include `case_results`; those
  aggregate-only reports can still be parsed, but per-case triage is limited.
  For accurate baseline diffs, regenerate baseline reports with v0.7.0 or later.
- `compare-reports` exit codes: `0` policy passes, `1` policy fails, `2` invalid
  input (missing file, invalid JSON, invalid policy).

### Safety

- Deterministic and local: compares two JSON reports and writes JSON/Markdown.
  No LLM calls, no network, no GitHub API, no telemetry, no hidden persistence.
- Deterministic transition classification only — not root-cause analysis, and no
  correctness guarantee.

## [0.6.0] - 2026-07-09

Theme: **agent adapter + live pack refresh**. Run your agent, capture the output,
refresh the pack, gate the regression.

### Added

- `AgentCommand`, `AgentRunInput`, `AgentRunResult`, `AgentAdapter` protocol, and
  `CommandAgentAdapter` (explicit local subprocess, no shell by default, timeout,
  minimal environment).
- `PackRefreshResult` and `RegressionPackRefresher` (`refresh_pack`,
  `refresh_pack_file`).
- Refresh JSON report helpers (`export_refresh_report`, `write_refresh_report`).
- `entropy-loop agent-demo` and `entropy-loop refresh-pack INPUT OUTPUT
  -- <command>` (exit codes: 0 refreshed, 1 agent-run failure, 2 bad input;
  optional `--json-report`, `--fail-fast`, `--timeout`).
- `examples/json_agent_agent.py`, `examples/agent_adapter_ci.py`, and
  `docs/agent-adapters.md`.

### Safety

- Entropy Loop Core runs a command only when explicitly given one; no implicit
  execution, no auto-discovery, no shell by default, no secret injection.
- The library makes no network calls; deterministic given adapter outputs.

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

[1.0.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v1.0.0
[0.9.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.9.0
[0.8.1]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.8.1
[0.8.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.8.0
[0.7.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.7.0
[0.6.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.6.0
[0.5.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.5.0
[0.4.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.4.0
[0.3.1]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.3.1
[0.3.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.3.0
[0.2.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.2.0
[0.1.0]: https://github.com/koreaelonmusk/entropy-loop-core/releases/tag/v0.1.0
