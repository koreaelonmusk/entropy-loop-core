# Architecture

Entropy Loop Core is a **Failure Compiler** for AI agents. Instead of blindly
retrying, it treats every failure as structured input and *compiles* it into
reusable artifacts: lessons that improve the next attempt and regression cases
that prevent the mistake from returning.

## The pipeline

```
Task ─▶ Agent ─▶ AgentOutput ─▶ Verifier ─▶ pass ─▶ LoopResult(success)
                                    │
                                   fail
                                    ▼
                              FailureTrace ──▶ MemoryStore
                                    │
                    ┌───────────────┼────────────────┐
                    ▼               ▼                 ▼
             LessonGenerator   RegressionGen     (retry with
              → Lesson          → RegressionCase   lessons in context)
```

Failure is not a dead end — it is the fuel for the next, better attempt.

## Data contract (`types.py`)

Pydantic models shared across every component:

- `Task` — the work item (`id`, `instruction`, `metadata`).
- `AgentOutput` — raw agent output (`content`, `metadata`).
- `VerificationResult` — the verdict (`passed`, `reason`, `rule_name`, `severity`).
- `FailureTrace` — a structured failure (`task`, `output`, `verification_result`,
  `attempt`, `timestamp`).
- `Lesson` — a compiled learning artifact (`summary`, `avoid_next_time`,
  `recommended_prompt_patch`, `tags`).
- `RegressionCase` — a test-like artifact (`name`, `instruction`,
  `expected_rule`, `failure_reason`).
- `AgentContext` — what the agent receives each attempt (`task`, `attempt`,
  `lessons`).
- `LoopResult` — the structured outcome (`status`, `attempts`, `output`,
  `failures`, `lessons`, `regression_cases`).
- `LoopStatus` / `Severity` — enums.

## Components

### Verifier (`verification.py`)

Applies an ordered list of rules to an `AgentOutput` and returns the first
`VerificationResult` that fails. A rule is any `Callable[[Task, AgentOutput],
VerificationResult]`. Built-in rule builders: `non_empty_output`,
`contains_required_terms`, `valid_json_when_expected`, and `max_length`.

### MemoryStore (`memory.py`)

In-memory accumulator for failure traces and lessons. Beyond simple recording it
offers `recent_failures` and `relevant_lessons(task)` — a deterministic keyword
overlap search so retries are fed the lessons that matter for the current task.

### LessonGenerator (`lessons.py`)

The compiler core. It maps a `FailureTrace` to a `Lesson` using fixed, per-rule
guidance. It is **deterministic and does no I/O — no LLM, no network** — so the
same failure always yields the same lesson.

### RegressionGenerator (`regression.py`)

Turns a `FailureTrace` into a `RegressionCase` with a stable, identifier-friendly
name, recording the rule that must pass for the failure to count as fixed.

### EntropyLoop (`loop.py`)

The orchestrator. Each attempt: build an `AgentContext` (with relevant lessons),
run the agent, verify. On success it returns; on failure it traces, compiles a
lesson, generates a regression case, remembers everything, and retries — up to
`max_attempts`. Agent exceptions are caught and traced as `CRITICAL` failures.

## Design principles

- **Failure-first.** The structured failure path is the product, not an afterthought.
- **Deterministic core.** Lessons and regressions are reproducible and testable.
- **Callables over inheritance.** Agents and rules are plain functions.
- **Typed boundaries.** Pydantic models keep every hand-off explicit.
- **No hidden state, no network.** Memory is passed in; nothing phones home.
