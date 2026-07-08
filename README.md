# Entropy Loop Core

**A Failure Compiler for AI agents.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)

Turn bad agent outputs into structured failure traces, reusable lessons, safer
retry context, evaluation summaries, and regression cases.

**Stop throwing failures away. Compile them.**

```bash
pip install -e ".[dev]"
entropy-loop demo
```

## The loop

```text
Task
  ↓
AgentOutput
  ↓
VerificationResult
  ↓
FailureTrace
  ↓
Lesson
  ↓
RetryContext
  ↓
LoopResult
  ↓
RegressionCase
```

## Core thesis

> AI agents become more reliable when failures are **captured**, **compressed
> into lessons**, and **reused** in future attempts.

This project is the smallest sharp primitive that proves that thesis — not a
large agent framework. It **captures, classifies, and summarizes** failures; it
does **not** train models or guarantee correctness.

## Why this exists

Most agent stacks showcase the happy path and bolt on ad-hoc retries. In
production the cost is in the *failures*: malformed tool calls, broken JSON,
hallucinated answers, the same mistake repeated, retries that spiral into cost,
and logs that pile up while nothing gets smarter. AI agents still have no black
box and no mistake notebook. Entropy Loop Core is that layer.

## What problem it solves

A retry library does `Agent → Output → Retry`. A Failure Compiler does:

```
Task → AgentOutput → VerificationResult → FailureTrace → FailureCategory
     → Lesson → RetryContext → LoopResult → RegressionCase → EvaluationSummary
```

Every failure is *compiled* into reusable assets:

1. **detect** bad outputs with explicit rules,
2. **classify** each failure by category (empty output, missing term, invalid
   JSON, too long, agent exception, …),
3. **store** each failure as a structured, fingerprinted trace,
4. **compile** traces into reusable lessons,
5. **retry** with those lessons in context,
6. **regress** — generate a case so the same failure can be checked later,
7. **summarize** the run into an evaluation summary.

The compiler itself is **deterministic and does no I/O — no LLM, no network** —
so your reliability layer is itself reliable, testable, and vendor-neutral. It
**captures, classifies, and summarizes** failures; it does **not** train models
or guarantee correctness.

## What's new in v0.2.0

- **Failure categories** — every `VerificationResult` carries a
  `FailureCategory` and structured `details`.
- **Verification policy** — configure rules declaratively with
  `VerificationPolicy` and `Verifier.from_policy(...)`.
- **Failure fingerprints** — a deterministic, public-safe hash on every trace so
  similar failures group without storing raw content.
- **Evaluation summary** — `summarize(result, cases)` rolls a run up into an
  `EvaluationSummary`.
- **Regression export** — `export_regression_case(s)` renders cases as plain dicts.
- **Sharper CLI** — `entropy-loop demo` shows category, fingerprint, and summary;
  new `entropy-loop doctor` health check.

## Features

- **Typed failure traces** — structured, fingerprinted records of what failed.
- **Deterministic verifier** — composable rules; no LLM, no network, no surprises.
- **In-memory lesson store** — remembers failures and recalls relevant lessons.
- **Retry context** — feeds prior failures and lessons into the next attempt.
- **Regression case generation** — pin failures so they can be checked later.
- **Evaluation summary** — a compact, public-safe rollup of each run.
- **CLI demo + doctor** — see the whole loop, and health-check the install.
- **Public-safe docs** — architecture, reliability model, and a clear boundary.

## Installation

Requires Python 3.10+.

```bash
pip install -e ".[dev]"
```

## Quickstart

```python
from entropy_loop_core import (
    AgentOutput,
    EntropyLoop,
    MemoryStore,
    RetryContext,
    Task,
    VerificationPolicy,
    Verifier,
    generate_regression_case,
    summarize,
)


def learning_agent(task: Task, ctx: RetryContext) -> AgentOutput:
    # No lessons yet -> omit the required term and fail. After the loop compiles
    # a lesson and feeds it back, adapt and succeed.
    if not ctx.lessons:
        return AgentOutput(content="Job finished.")
    return AgentOutput(content="status: done - job finished.")


memory = MemoryStore()
policy = VerificationPolicy(require_non_empty=True, required_terms=["status"])
loop = EntropyLoop(verifier=Verifier.from_policy(policy), memory=memory, max_attempts=3)

result = loop.run(Task(id="t1", instruction="report the job status"), learning_agent)

print(result.status)                      # success
print(result.attempts)                    # 2
print(result.output.content)              # status: done - job finished.
print(result.failures[0].category)        # missing_required_term
print(result.failures[0].fingerprint)     # deterministic public-safe hash
print(result.lessons[0].summary)          # the compiled lesson

cases = [generate_regression_case(t) for t in result.failures]
print(summarize(result, cases).model_dump())  # evaluation summary
```

## CLI demo

```bash
entropy-loop demo
```

```text
Entropy Loop Demo
1. Task started: 'report the job status'
2. Attempt 1 failed: missing required terms: ['status']
3. Failure category: missing_required_term
4. Failure fingerprint: fd46a1fcda19a179
5. Lesson generated
6. Retry context updated
7. Attempt 2 passed
8. Evaluation summary: status=success, attempts=2, failures=1, categories={'missing_required_term': 1}
9. Regression case generated: regression_report_the_job_status_contains_required_terms
```

A health check is also available:

```bash
entropy-loop doctor
```

See [examples/failure_compiler_demo.py](examples/failure_compiler_demo.py). To
record a demo GIF, see [docs/demo.md](docs/demo.md).

## Architecture

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
              → Lesson                         RetryContext
```

- **`EntropyLoop`** orchestrates verify → trace → learn → retry.
- **`Verifier`** applies ordered rules and reports the first violation.
- **`LessonGenerator`** compiles failure traces into reusable lessons.
- **`MemoryStore`** remembers failures and recalls relevant lessons.
- **`generate_regression_case`** turns a failure into a test-like case.

Details in [docs/architecture.md](docs/architecture.md); the reliability model in
[docs/reliability-model.md](docs/reliability-model.md).

## Public / private boundary

> **Entropy Loop Core open-sources the primitive, not the private advantage.**

This repository contains only generic reliability primitives. It deliberately
excludes business logic, proprietary prompts, customer data, private benchmarks,
cloud sync, auth, billing, dashboards, and any external network or AI API calls.
Commercial products may build private policies, datasets, dashboards, and
deployment workflows on top of this core. See
[docs/public-private-boundary.md](docs/public-private-boundary.md).

## Design principles

- **Failure-first.** The structured failure path is the product.
- **Deterministic core.** Lessons and regressions are reproducible and testable.
- **Karpathy-style simplicity.** Obvious names, small files, explicit control flow.
- **Ponytail principle.** One sharp primitive before many blurry features.
- **Typed boundaries.** Pydantic models at every hand-off.
- **No hidden state, no network.** Memory is passed in; nothing phones home.

This does not perform model training or guarantee correctness; it captures
failures, generates reusable lessons, improves retry context, and helps prevent
repeated failures through regression cases.

## Releases

- **v0.2.0** — failure classification, verification policy, fingerprints,
  evaluation summary, and regression export. *(current)*
- **v0.1.0** — the first public Failure Compiler loop: verify, trace, learn,
  retry, regress.

See [CHANGELOG.md](CHANGELOG.md) for details.

## Roadmap

- **v0.3.0 (directional)** — *replay*: turn regression cases into a runnable
  suite so a remembered failure can be re-checked, not just stored.
- **v0.4.0 (directional)** — *memory policy*: what to remember, group, and forget.
- **Later** — async, pluggable verifier registry, persistence adapters, richer
  evaluation reports, integrations.

The reliability model is documented in
[docs/reliability-model.md](docs/reliability-model.md); full plan in
[docs/roadmap.md](docs/roadmap.md).

## Development

```bash
ruff check .        # lint
ruff format .       # format
pytest              # tests
```

## Contributing

Contributions are welcome. Please keep the core small, readable, and
deterministic, and respect the public/private boundary. See
[CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Released under the [Apache-2.0](LICENSE) license.

## Maintainer note

Entropy Loop Core is maintained as an open-source project and intentionally kept
small, readable, and deterministic. It is the public seed of a larger AI
ecosystem: the open core is the primitive; the private advantage — operational
data, advanced policies, product loops, and enterprise UX — is built separately.
Issues and pull requests are welcome.
