# Reliability Model

This document explains, in generic and public-safe terms, how Entropy Loop Core
turns a single agent failure into reusable reliability signal. It is a mental
model, not a correctness guarantee — the core **captures**, **classifies**, and
**summarizes** failures; it does not train models or promise correctness.

The v0.2.0 loop:

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

## 1. Failure classification

A verification failure is not just "it failed" — it has a **kind**. Each
`VerificationResult` carries a `FailureCategory` and structured, non-sensitive
`details`. The starting taxonomy is deliberately small and non-universal:

| Category | Meaning |
|---|---|
| `empty_output` | The output was empty or whitespace-only. |
| `missing_required_term` | A required term was absent. |
| `invalid_json` | JSON was expected but did not parse. |
| `too_long` | The output exceeded the allowed length. |
| `agent_exception` | The agent raised instead of returning. |
| `unknown` | Anything not otherwise classified. |

Classification is what turns a pile of failures into something you can count,
group, and reason about.

## 2. Verification policy

Rules can be configured declaratively with a `VerificationPolicy` and built with
`Verifier.from_policy(...)` — a convenience layer over the fluent `Verifier`
API, not a framework. The same four rules are available either way:
non-empty, required terms, JSON, and length.

```python
policy = VerificationPolicy(require_non_empty=True, required_terms=["status"])
verifier = Verifier.from_policy(policy)
```

## 3. Fingerprinting

Every `FailureTrace` exposes a deterministic `fingerprint`: a hash derived from
the task-instruction hash plus the rule name, category, and reason. It groups
similar failures **without storing raw content** — the fingerprint is a hash,
never the underlying text. Same inputs always produce the same fingerprint.

## 4. Lesson generation

`LessonGenerator` maps a failure — keyed by its category — to a reusable
`Lesson` with a summary, what to avoid, and a recommended prompt patch. It is
deterministic: **no LLM, no network, no randomness**. The same failure always
compiles to the same lesson.

## 5. Retry context

On retry, the agent receives a `RetryContext` carrying prior failures and the
lessons relevant to the task. This is how a captured failure improves the next
attempt — explicitly, through context, not through any model update.

## 6. Regression cases

A `RegressionCase` pins a task that once failed together with the rule that must
pass for the failure to be considered fixed. `export_regression_case(s)` renders
cases as plain dictionaries so they can be serialized. This is how a one-time fix
becomes a durable check.

## 7. Evaluation summary

`summarize(result, cases)` rolls a run up into a compact `EvaluationSummary`:
attempts, success, failure count, a breakdown of failures by category, the final
status, and how many regression cases were generated. It is a plain data object
— **no dashboards, no charts, no telemetry, nothing phones home**.

## 8. Replay

Generating a regression case is only half the value; the other half is being
able to **run it again**. A `RegressionSuite` groups cases, and `RegressionRunner`
replays each one: it turns the case back into a task, runs the agent once,
verifies, and records pass/fail in a `RegressionReport` (with a `success_rate`).

This closes the loop: a past failure becomes a repeatable check you can run
before the same agent bug ships again. Suites can be saved to and loaded from
local JSON, so a corpus of past failures persists across runs. Replay is
**deterministic regression checking** — no retries inside the runner, no network,
no model training, and no correctness guarantee.

A `RegressionPack` takes this further: it bundles cases, a verification policy,
and reference outputs into a portable file that runs in CI via
`entropy-loop run-pack`, with stable exit codes so a reappearing regression fails
the build. See [regression-packs.md](regression-packs.md).

## 9. Memory hygiene

Generating a lesson per failure is only useful until memory fills with
near-duplicates. A `MemoryPolicy` and `LessonCompactor` decide what to keep,
merge, and drop: drop empty lessons, deduplicate by guidance fingerprint or
failure category, enforce a minimum occurrence count, and cap how many lessons
are retained. Compaction is **deterministic** — a fixed-template summary, no
model calls, no network, no hidden persistence. It is memory hygiene, not
learning. See [memory-policy.md](memory-policy.md).

## What this is not

- Not model training or self-improvement of weights.
- Not a correctness or safety guarantee.
- Not a universal failure taxonomy — the categories are a small starting set.

Commercial products may build private policies, datasets, dashboards, and
deployment workflows on top of this open-source core. Those live elsewhere; see
[public-private-boundary.md](public-private-boundary.md).
