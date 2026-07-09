# Architecture

Entropy Loop Core is a **Failure Compiler** for AI agents. Instead of blindly
retrying, it treats every failure as structured input and *compiles* it into
reusable artifacts: lessons that improve the next attempt and, on demand,
regression cases that pin the mistake so it can be checked later.

## The core loop

Understandable in one glance:

```txt
Task
  → AgentOutput
  → VerificationResult
  → FailureTrace
  → FailureCategory
  → Lesson
  → RetryContext
  → LoopResult
  → RegressionCase
  → EvaluationSummary
```

```
Task ─▶ Agent ─▶ AgentOutput ─▶ Verifier ─▶ pass ─▶ LoopResult(success)
                                    │
                                   fail
                                    ▼
                              FailureTrace ──▶ MemoryStore
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                                ▼
             LessonGenerator                  retry with a
              → Lesson  ──▶ MemoryStore ──▶   RetryContext (prior
                                              failures + lessons)

  generate_regression_case(trace) ──▶ RegressionCase   (on demand)
```

Failure is not a dead end — it is the fuel for the next, better attempt.

## Object model (`types.py`)

Pydantic models shared across every component:

- `Task` — the work item (`id`, `instruction`, `metadata`).
- `AgentOutput` — raw agent output (`content`, `metadata`).
- `VerificationResult` — the verdict (`passed`, `reason`, `rule_name`, `severity`,
  `category`, `details`).
- `FailureTrace` — a structured failure (`task`, `output`, `verification_result`,
  `attempt`, `timestamp`) plus derived `category` and `fingerprint`.
- `Lesson` — a compiled learning artifact (`summary`, `avoid_next_time`,
  `recommended_prompt_patch`, `tags`).
- `RetryContext` — what a retry receives (`attempt`, `prior_failures`, `lessons`).
- `LoopResult` — the outcome (`status`, `attempts`, `output`, `failures`,
  `lessons`, `errors`).
- `RegressionCase` — a test-like artifact (`name`, `instruction`,
  `expected_rule`, `failure_reason`, `category`).
- `EvaluationSummary` — a run rollup (`total_attempts`, `success`,
  `failure_count`, `categories`, `final_status`, `generated_regression_cases`).
- `RegressionSuite` — a named collection of `RegressionCase`s.
- `RegressionRunResult` — the outcome of replaying one case (`passed`, `output`,
  `verification_result`, `error`).
- `RegressionReport` — a replay rollup (`suite_name`, `total_cases`, `passed`,
  `failed`, `results`, and a computed `success_rate`).
- `Severity` / `Status` / `FailureCategory` — string literals, not enums, to keep
  the contract plain.

## Module responsibilities

### `verification.py` — `Verifier`, `VerificationPolicy`

A fluent builder of simple, deterministic rules applied in order to an
`AgentOutput`. `require_non_empty`, `require_terms`, `expect_json`, `max_length`.
`verify(output)` returns the first failing `VerificationResult`, classified with
a `FailureCategory` and structured `details`. `VerificationPolicy` +
`Verifier.from_policy(...)` configure the same rules declaratively. No I/O.

### `memory.py` — `MemoryStore`

In-memory accumulator for failures and lessons: `add_failure`, `add_lesson`,
`recent_failures`, `all_lessons`, and `relevant_lessons(task)` — a deterministic
keyword-overlap recall so retries get the lessons that matter. No database, no
vector store, no embeddings.

### `lessons.py` — `LessonGenerator`

The compiler core. Maps a `FailureTrace` to a `Lesson` using fixed guidance
keyed by the failure's `FailureCategory`. **Deterministic and side-effect free —
no LLM, no network** — so the same failure always yields the same lesson.

### `regression.py` — `generate_regression_case`, export/import helpers

Pure functions turning a `FailureTrace` into a `RegressionCase` with a stable,
identifier-friendly name, and rendering cases, suites, and reports as plain
dictionaries. Includes local-filesystem JSON `save_regression_suite` /
`load_regression_suite` — no network, no database.

### `replay.py` — `RegressionRunner`

Replays regression cases. `run_case` turns a `RegressionCase` back into a task,
runs the agent once (attempt 1, no lessons), verifies, and returns pass/fail;
`run_suite` aggregates a `RegressionReport`. Deterministic, no retries, no
network. Agent exceptions are caught and reported as failures.

### `memory_policy.py` — `LessonCompactor`

Applies a `MemoryPolicy` to a list of lessons and returns a `CompactionResult`:
drops empty/low-signal lessons, deduplicates by guidance fingerprint or failure
category, and caps how many lessons are retained. Deterministic and side-effect
free — no LLM, no network, no database. See [memory-policy.md](memory-policy.md).

### `regression_pack.py` — `RegressionPack`, `RegressionPackRunner`

A `RegressionPack` bundles cases with a `VerificationPolicy` and reference
outputs into a portable JSON file. `RegressionPackRunner` replays it (reusing
`RegressionRunner`) into a `RegressionPackResult`, with JSON/JUnit report
writers. The CLI `entropy-loop run-pack` returns stable exit codes (0/1/2) so a
reappearing regression fails CI. See [regression-packs.md](regression-packs.md).

### `agent_adapter.py` — `CommandAgentAdapter`, `RegressionPackRefresher`

An `AgentAdapter` produces a candidate output for a case; `CommandAgentAdapter`
does so by running an explicit local `AgentCommand` (subprocess, no shell,
timeout, minimal env). `RegressionPackRefresher` refreshes a pack's outputs from
an adapter into a new pack. The CLI `entropy-loop refresh-pack ... -- <command>`
runs your agent and writes a refreshed pack for `run-pack` to gate. See
[agent-adapters.md](agent-adapters.md).

### `triage.py` — `RegressionTriageEngine`

Deterministic baseline-vs-current diffing. Given two `run-pack` JSON reports, it
joins their per-case `case_results` by case id and classifies each transition
(newly failing, fixed, persistent, skipped, missing) into a `RegressionTriage`. A
`TriagePolicy` decides the CI outcome (`new-failures` by default). The CLI
`entropy-loop compare-reports BASELINE CURRENT` writes JSON/Markdown and returns
stable exit codes. Local-only: no network, no GitHub API. See
[regression-triage.md](regression-triage.md).

### `ci_evidence.py` — `CIEvidenceWriter`

Turns a `RegressionTriage` into a deterministic local evidence directory
(`triage.json`, `triage.md`, `summary.txt`, `manifest.json`) and, on request,
appends a compact GitHub Actions step summary (reading only `GITHUB_STEP_SUMMARY`).
The CLI `entropy-loop write-ci-evidence` and the root `action.yml` composite
Action wire this into CI. No GitHub API, no token, no network. See
[ci-evidence.md](ci-evidence.md).

### `evaluation.py` — `summarize`

A pure function that rolls a `LoopResult` (and any generated regression cases)
up into an `EvaluationSummary`. No dashboards, no telemetry.

### `loop.py` — `EntropyLoop`

The orchestrator. Each attempt: build a `RetryContext`, run the agent
(`(task, context) -> AgentOutput | str`), verify. On success it returns; on
failure it classifies, traces, compiles a lesson, remembers both, and retries —
up to `max_attempts`. Agent exceptions are caught and traced as `critical`,
`agent_exception` failures.

### `cli.py` — `entropy-loop`

A Typer CLI: `demo` narrates the whole pipeline (including category, fingerprint,
and evaluation summary) end to end; `replay-demo` generates a regression case and
replays it as a suite; `doctor` runs basic health checks.

## Why the core stays intentionally small

This project proves one thesis — *failures captured, classified, compressed into
lessons, and reused make agents more reliable* — with the smallest sharp
primitive. It has **no** async, plugin system, tool execution, nested agents,
persistence, vector search, or network. Those are deliberately deferred (see
[roadmap.md](roadmap.md)) so the central path stays beautiful and readable.
