# Entropy Loop Core

**A Failure Compiler for AI agents.** It turns bad outputs into failure traces,
lessons, retries, and regression cases.

> Entropy Loop Core is an open-source Failure Compiler for AI agents. It turns
> bad outputs into failure traces, lessons, retries, and regression cases.

## Core thesis

> AI agents become more reliable when failures are **captured**, **compressed
> into lessons**, and **reused** in future attempts.

This project is the smallest sharp primitive that proves that thesis — not a
large agent framework.

## Why this exists

Most agent stacks showcase the happy path and bolt on ad-hoc retries. In
production the cost is in the *failures*: malformed tool calls, broken JSON,
hallucinated answers, the same mistake repeated, retries that spiral into cost,
and logs that pile up while nothing gets smarter. AI agents still have no black
box and no mistake notebook. Entropy Loop Core is that layer.

## What problem it solves

A retry library does `Agent → Output → Retry`. A Failure Compiler does:

```
Task → AgentOutput → VerificationResult → FailureTrace → Lesson → RetryContext → LoopResult → RegressionCase
```

Every failure is *compiled* into reusable assets:

1. **detect** bad outputs with explicit rules,
2. **explain** why they failed (a named rule and a severity),
3. **store** each failure as a structured trace,
4. **compile** traces into reusable lessons,
5. **retry** with those lessons in context,
6. **regress** — generate a case so the same failure can be checked later.

The compiler itself is **deterministic and does no I/O — no LLM, no network** —
so your reliability layer is itself reliable, testable, and vendor-neutral.

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
    Verifier,
    generate_regression_case,
)


def learning_agent(task: Task, ctx: RetryContext) -> AgentOutput:
    # No lessons yet -> omit the required term and fail. After the loop compiles
    # a lesson and feeds it back, adapt and succeed.
    if not ctx.lessons:
        return AgentOutput(content="Job finished.")
    return AgentOutput(content="status: done - job finished.")


memory = MemoryStore()
verifier = Verifier().require_non_empty().require_terms(["status"])
loop = EntropyLoop(verifier=verifier, memory=memory, max_attempts=3)

result = loop.run(Task(id="t1", instruction="report the job status"), learning_agent)

print(result.status)                      # success
print(result.attempts)                    # 2
print(result.output.content)              # status: done - job finished.
print(result.lessons[0].summary)          # the compiled lesson
print(generate_regression_case(result.failures[0]).name)  # a regression case
```

## CLI demo

```bash
entropy-loop demo
```

```text
Entropy Loop Demo
1. Running task...
2. Attempt 1 failed: missing required terms: ['status']
3. Failure trace stored
4. Lesson generated
5. Retrying with lesson context
6. Attempt 2 passed
7. Loop completed successfully
```

See [examples/failure_compiler_demo.py](examples/failure_compiler_demo.py).

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

Details in [docs/architecture.md](docs/architecture.md); the reasoning in
[docs/research/failure-compiler-theory.md](docs/research/failure-compiler-theory.md).

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

## Roadmap

- **v0.1.0** — Failure Compiler foundations: verify, trace, learn, retry, regress. *(current)*
- **Future (not now)** — async, pluggable verifier registry, persistence
  adapters, evaluation reports, integrations, advanced policies.

Full plan in [docs/roadmap.md](docs/roadmap.md).

## Development

```bash
ruff check .        # lint
ruff format .       # format
pytest              # tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Released under the [Apache-2.0](LICENSE) license.

## Maintainer note

Entropy Loop Core is maintained as an open-source project and intentionally kept
small, readable, and deterministic. It is the public seed of a larger AI
ecosystem: the open core is the primitive; the private advantage — operational
data, advanced policies, product loops, and enterprise UX — is built separately.
Issues and pull requests are welcome.
