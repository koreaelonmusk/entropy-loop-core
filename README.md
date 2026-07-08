# Entropy Loop Core

**A Failure Compiler for AI agents.** Turn failed agent outputs into regression
cases and replay them before the same bug ships again.

[![CI](https://github.com/koreaelonmusk/entropy-loop-core/actions/workflows/ci.yml/badge.svg)](https://github.com/koreaelonmusk/entropy-loop-core/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)

[Get started](#get-started) · [Example](#example) · [CLI](#cli) · [Architecture](#architecture) · [Releases](#releases) · [Contributing](#contributing)

![Entropy Loop Core replay demo](./docs/assets/demo.gif)

## Get started

Install from source (a package-index install is planned after stabilization):

```bash
git clone https://github.com/koreaelonmusk/entropy-loop-core.git
cd entropy-loop-core
python -m pip install -e ".[dev]"
entropy-loop replay-demo
```

Works on Windows, macOS, and Linux with Python 3.10+.

## Why

AI agents often fail the same way twice.

Entropy Loop Core makes failures reusable: capture the failed output, classify
it, compile a lesson, generate a regression case, and replay it — before the
same bug ships again.

```text
Task
→ AgentOutput
→ VerificationResult
→ FailureTrace
→ Lesson
→ RegressionCase
→ RegressionSuite
→ Replay
→ Report
```

The core is deterministic: no LLM calls, no network calls, no hidden state.

## Example

Turn a failure into a regression case, then replay it against a fixed agent:

```python
from entropy_loop_core import (
    AgentOutput,
    FailureTrace,
    RegressionRunner,
    RegressionSuite,
    RetryContext,
    Task,
    VerificationPolicy,
    Verifier,
    generate_regression_case,
)

# A verifier built from a policy: non-empty output that contains "status".
verifier = Verifier.from_policy(
    VerificationPolicy(require_non_empty=True, required_terms=["status"])
)

# A past failure (the agent omitted "status") becomes a regression case.
task = Task(id="job-1", instruction="report the job status")
bad = AgentOutput(content="done")
case = generate_regression_case(
    FailureTrace(
        task=task,
        output=bad,
        verification_result=verifier.verify(bad),
        attempt=1,
    )
)


# Replay the case against a corrected agent.
def fixed_agent(task: Task, ctx: RetryContext) -> AgentOutput:
    return AgentOutput(content="status: ok")


report = RegressionRunner().run_suite(
    RegressionSuite(name="job", cases=[case]), fixed_agent, verifier
)
print(report.passed, report.total_cases, report.success_rate)  # 1 1 100.0
```

Full worked example: [examples/json_agent_guard.py](examples/json_agent_guard.py).

## CLI

```bash
entropy-loop replay-demo   # generate a regression case, then replay it as a suite
entropy-loop demo          # run the loop: verify → trace → learn → retry → regress
entropy-loop doctor        # health-check the install
```

## What it is / what it is not

**It is**

- a deterministic failure compiler,
- a structured failure-trace layer,
- a regression replay primitive,
- a small AI-agent reliability tool.

**It is not**

- a full agent framework,
- model training,
- model-as-judge by default,
- a correctness guarantee,
- a cloud platform.

## Architecture

- **`Verifier`** applies ordered, deterministic rules and classifies failures.
- **`EntropyLoop`** runs an agent, verifies, traces the failure, compiles a
  lesson, and retries.
- **`LessonGenerator`** turns a `FailureTrace` into a reusable `Lesson`.
- **`generate_regression_case`** pins a failure as a repeatable check.
- **`RegressionRunner`** replays a `RegressionSuite` and returns a report.

Deeper reading: [architecture](docs/architecture.md) ·
[reliability model](docs/reliability-model.md) ·
[research influences](docs/research-influences.md) ·
[recording the demo](docs/demo.md).

## Public / private boundary

> **Open-source the primitive, not the private advantage.**

This repository contains only generic reliability primitives — no business logic,
proprietary prompts, customer data, secrets, external AI API calls, or network
calls. See [docs/public-private-boundary.md](docs/public-private-boundary.md).

## Releases

- **v0.3.0** — replay *(current)*
- **v0.2.0** — classification + evaluation
- **v0.1.0** — the first Failure Compiler loop

Details in [CHANGELOG.md](CHANGELOG.md).

## Roadmap

- **v0.3.1** — stabilization / packaging readiness
- **v0.4.0** — memory policy / lesson compaction
- **Later** — persistence adapters and richer reports

Full plan in [docs/roadmap.md](docs/roadmap.md).

## Contributing

Contributions are welcome. Keep the core small, readable, and deterministic, and
respect the public/private boundary. See [CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

```bash
ruff check .    # lint
ruff format .   # format
pytest          # tests
```

## License

Released under the [Apache-2.0](LICENSE) license.
