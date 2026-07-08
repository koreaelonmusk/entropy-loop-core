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
  → Lesson
  → RetryContext
  → LoopResult
  → RegressionCase
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
- `VerificationResult` — the verdict (`passed`, `reason`, `rule_name`, `severity`).
- `FailureTrace` — a structured failure (`task`, `output`, `verification_result`,
  `attempt`, `timestamp`).
- `Lesson` — a compiled learning artifact (`summary`, `avoid_next_time`,
  `recommended_prompt_patch`, `tags`).
- `RetryContext` — what a retry receives (`attempt`, `prior_failures`, `lessons`).
- `LoopResult` — the outcome (`status`, `attempts`, `output`, `failures`,
  `lessons`, `errors`).
- `RegressionCase` — a test-like artifact (`name`, `instruction`,
  `expected_rule`, `failure_reason`).
- `Severity` / `Status` — string literals, not enums, to keep the contract plain.

## Module responsibilities

### `verification.py` — `Verifier`

A fluent builder of simple, deterministic rules applied in order to an
`AgentOutput`. `require_non_empty`, `require_terms`, `expect_json`, `max_length`.
`verify(output)` returns the first failing `VerificationResult`. No I/O.

### `memory.py` — `MemoryStore`

In-memory accumulator for failures and lessons: `add_failure`, `add_lesson`,
`recent_failures`, `all_lessons`, and `relevant_lessons(task)` — a deterministic
keyword-overlap recall so retries get the lessons that matter. No database, no
vector store, no embeddings.

### `lessons.py` — `LessonGenerator`

The compiler core. Maps a `FailureTrace` to a `Lesson` using fixed, per-rule
guidance. **Deterministic and side-effect free — no LLM, no network** — so the
same failure always yields the same lesson.

### `regression.py` — `generate_regression_case`

A pure function turning a `FailureTrace` into a `RegressionCase` with a stable,
identifier-friendly name.

### `loop.py` — `EntropyLoop`

The orchestrator. Each attempt: build a `RetryContext`, run the agent
(`(task, context) -> AgentOutput | str`), verify. On success it returns; on
failure it traces, compiles a lesson, remembers both, and retries — up to
`max_attempts`. Agent exceptions are caught and traced as `critical` failures.

### `cli.py` — `entropy-loop`

A Typer CLI whose `demo` command narrates the whole pipeline end to end.

## Why v0.1.0 is intentionally small

This release proves one thesis — *failures captured, compressed into lessons,
and reused make agents more reliable* — with the smallest sharp primitive. It
has **no** async, plugin system, tool execution, nested agents, persistence,
vector search, or network. Those are deliberately deferred (see
[roadmap.md](roadmap.md)) so the central path stays beautiful and readable.
