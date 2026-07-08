# Entropy Loop Core

**A Failure Compiler for AI agents.** It turns bad outputs into failure traces,
lessons, retries, and regression cases.

> Entropy Loop Core is an open-source Failure Compiler for AI agents. It turns
> bad outputs into failure traces, lessons, retries, and regression cases.

## What problem this solves

AI agents are probabilistic: the same task can succeed once and fail the next
time. Most stacks bolt on ad-hoc retries and scattered validation, log the mess,
and forget everything the moment a run ends. Nothing gets smarter.

In production, the cost is not in the successes — it is in the failures:

- malformed tool calls,
- broken JSON,
- hallucinated answers,
- the same mistake repeated,
- retries that spiral into cost,
- logs that pile up while no learning happens.

The gap is clear: **AI agents still have no black box and no mistake notebook.**
Entropy Loop Core is that layer.

## Why failure-first reliability matters

A retry library does `Agent → Output → Retry`.

A Failure Compiler does:

```
Agent → Output → Verify → Failure Trace → Lesson → Memory → Better Retry → Regression Test
```

Every failure is *compiled* into reusable assets:

1. **detect** bad outputs with explicit rules,
2. **explain** why they failed (a named rule and a severity),
3. **store** each failure as a structured trace,
4. **compile** traces into reusable lessons,
5. **retry** with those lessons in context,
6. **regress** — optionally emit a case so the same failure never returns.

The compiler itself is **deterministic and does no I/O — no LLM, no network** —
so your reliability layer is itself reliable, testable, and vendor-neutral.

## Features

- **Structured failures** — `FailureTrace` captures task, output, verdict, and attempt.
- **Verification** — composable `Verifier` rules (non-empty, required terms, JSON, length).
- **Failure compilation** — `LessonGenerator` turns traces into reusable lessons, deterministically.
- **Memory with recall** — `MemoryStore` remembers failures and surfaces relevant lessons.
- **Regression cases** — `RegressionGenerator` pins failures so they can be checked forever.
- **The loop** — `EntropyLoop` runs, verifies, traces, learns, and retries.
- **Typed contracts** — Pydantic models at every boundary.
- **Tiny CLI** — `entropy-loop demo` shows the whole pipeline end to end.

## Installation

Requires Python 3.10+.

```bash
pip install -e ".[dev]"
```

## Quickstart

```bash
entropy-loop demo
```

```text
▶ Task [demo-001]: 'summarize the release notes'
  ✗ attempt 1 failed [non_empty_output/error]: output is empty
  ⚙ compiled lesson: On task 'summarize the release notes', attempt 1 failed ...
      patch: Always produce a concrete, non-empty answer before returning.
  🧪 regression case: regression_summarize_the_release_notes_non_empty_output ...

Status:   success
Attempts: 2
Output:   'Draft summary for: summarize the release notes'
```

## Example

```python
from entropy_loop_core import (
    AgentContext,
    AgentOutput,
    EntropyLoop,
    MemoryStore,
    Task,
    Verifier,
)


def learning_agent(ctx: AgentContext) -> AgentOutput:
    # No lessons yet -> empty output, which fails verification.
    # After the loop compiles a lesson and feeds it back, adapt and succeed.
    if not ctx.lessons:
        return AgentOutput(content="")
    return AgentOutput(content=f"Answer for: {ctx.task.instruction}")


memory = MemoryStore()
loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=3)

result = loop.run(Task(instruction="explain entropy loops"), learning_agent)

print(result.status.value)              # success
print(result.attempts)                  # 2
print(result.output.content)            # Answer for: explain entropy loops
print(result.lessons[0].summary)        # the compiled lesson
print(result.regression_cases[0].name)  # the generated regression case
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
                    ┌───────────────┼────────────────┐
                    ▼               ▼                 ▼
             LessonGenerator   RegressionGen     retry with
              → Lesson          → RegressionCase  lessons in context
```

- **`EntropyLoop`** orchestrates verify → trace → learn → retry.
- **`Verifier`** applies ordered rules and reports the first violation.
- **`LessonGenerator`** compiles failure traces into reusable lessons.
- **`RegressionGenerator`** turns failures into test-like regression cases.
- **`MemoryStore`** remembers failures and recalls relevant lessons.

Details in [docs/architecture.md](docs/architecture.md) and the reasoning in
[docs/philosophy.md](docs/philosophy.md).

## What is open source

This repository is the **open-source core** — the reliability primitives every
agent needs, small enough to read every line:

- typed data contract,
- rule-based verification,
- deterministic lesson compilation,
- failure memory and lesson recall,
- regression-case generation,
- the retry-with-memory loop, and a CLI.

## What is intentionally not included

To keep the core clean and trustworthy, this project deliberately excludes:

- proprietary or business-specific logic,
- LLM prompts, model calls, or any network I/O,
- customer data or credentials,
- paid dashboards, cloud sync, or enterprise features.

The core stays deterministic, dependency-light, and vendor-neutral.

## Roadmap

- **v0.1.0** — Failure Compiler foundations: verify, trace, learn, retry, regress. *(current)*
- **v0.2.0** — sharper compilation from repeated failures; prompt-patch helpers.
- **v0.3.0** — regression as a first-class workflow; pluggable persistence.

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
small, readable, and deterministic. It contains no proprietary logic — just the
primitives that turn agent failures into assets. Issues and pull requests are
welcome.
