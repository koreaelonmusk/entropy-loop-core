# Entropy Loop Core

**An open-source reliability layer for AI agents.** It helps agents remember
failures, verify outputs, and improve through feedback loops.

## Why this exists

AI agents are probabilistic: the same task can succeed once and fail the next
time. Most agent stacks bolt on ad-hoc retries and scattered validation, then
forget everything the moment a run ends. Entropy Loop Core provides a small,
explicit reliability layer instead — one that verifies each output, remembers
what went wrong, and retries with that context. It is deliberately minimal,
dependency-light, and free of any vendor- or business-specific logic, so you can
drop it into any agent and read every line.

## Features

- **Memory** — `MemoryStore` records failures and lessons for inspection.
- **Verification** — `Verifier` validates outputs against composable rules.
- **Retry loop** — `EntropyLoop` runs, verifies, remembers, and retries.
- **Typed contracts** — Pydantic `Task` / `LoopResult` objects at the edges.
- **Framework-agnostic** — an agent is just a callable you provide.
- **Tiny CLI** — `entropy-loop demo` shows the loop end to end.

## Installation

Requires Python 3.10+.

```bash
pip install -e ".[dev]"
```

## Quickstart

```python
from entropy_loop_core import EntropyLoop, MemoryStore, Task, Verifier


def flaky_agent(task: Task, attempt: int) -> str:
    # Fails on the first attempt, succeeds afterwards.
    if attempt == 1:
        return ""
    return f"Answer for: {task.prompt}"


memory = MemoryStore()
loop = EntropyLoop(verifier=Verifier(), memory=memory, max_attempts=3)

result = loop.run(Task(prompt="explain entropy loops"), flaky_agent)

print(result.status.value)   # success
print(result.attempts)       # 2
print(result.output)         # Answer for: explain entropy loops
print(memory.failures())     # [Failure(attempt=1, reason='output is empty')]
```

Try the CLI demo:

```bash
entropy-loop demo
```

## Architecture

```
        ┌─────────────┐
Task ──▶ │ EntropyLoop │ ──▶ LoopResult
        └──────┬──────┘
               │ uses
     ┌─────────┼──────────┐
     ▼         ▼          ▼
 Verifier  MemoryStore   Agent
 (rules)   (failures/    (your callable)
            lessons)
```

- **`EntropyLoop`** orchestrates run → verify → remember → retry.
- **`Verifier`** applies ordered rules and reports the first violation.
- **`MemoryStore`** accumulates failures and lessons in memory.
- **Agent** is any `Callable[[Task, int], str]` you supply.

See [docs/architecture.md](docs/architecture.md) for details.

## Roadmap

- **v0.1.0** — foundations: memory, verification, retry loop, CLI. *(current)*
- **v0.2.0** — feed remembered failures back into retries; derive lessons.
- **v0.3.0** — pluggable persistence (file, SQLite); optional async loop.

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

Entropy Loop Core is maintained as an open-source project and intentionally
kept small and readable. It contains no proprietary logic — just the reliability
primitives every agent needs. Issues and pull requests are welcome.
