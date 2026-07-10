<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/haetae/haetae_readme_hero_dark.png">
    <img src="docs/assets/haetae/haetae_readme_hero.png" alt="Entropy Loop Core — Haetae guardian pixel mascot with the Failure to Evidence to Regression Test to CI Gate to Stable Contract pipeline, and JSON, Markdown, JUnit XML, HTML console, and GitHub Action outputs" width="760">
  </picture>
</p>

<h1 align="center">Entropy Loop Core</h1>

<p align="center">
  <b>AI agents fail in loops.</b> Entropy Loop turns those failures into tests, CI
  evidence, JUnit reports, HTML failure consoles, and stable contracts.
</p>

<p align="center">
  <sub><b>한국어:</b> Entropy Loop는 AI 에이전트 실패를 테스트, CI 증거, JUnit 리포트,
  사람이 읽는 실패 콘솔, 안정성 계약으로 변환합니다.</sub>
</p>

[![PyPI](https://img.shields.io/pypi/v/entropy-loop-core.svg)](https://pypi.org/project/entropy-loop-core/)
[![CI](https://github.com/koreaelonmusk/entropy-loop-core/actions/workflows/ci.yml/badge.svg)](https://github.com/koreaelonmusk/entropy-loop-core/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)

[Get started](#get-started) · [Example](#example) · [Output surfaces](#output-surfaces) · [CLI](#cli) · [Haetae Guardian](#haetae-guardian) · [Releases](#releases)

> Star the repo if you want to follow the Failure Compiler roadmap.

![Entropy Loop Core replay demo](./docs/assets/demo.gif)

Verify agent outputs, capture failures, compile them into regression cases, and
gate CI on them — then read the result three ways:

- **Machines read JUnit.** `--junit-report` emits CI-native XML for GitHub
  Actions, GitLab CI, Jenkins, CircleCI, and other test reporters.
- **Humans read the Pixel Failure Console.** `--html-report` writes a
  self-contained HTML report — inline CSS only, no network, no JS.
- **Teams read the Stability Contract.** `entropy-loop contract` declares the
  public API, CLI, exit codes, evidence bundle, and boundaries as JSON.

```text
┌─ Entropy Loop Failure Console ──────────────────────────────┐
│ AI agent regressions as CI evidence                         │
│                                                             │
│   TOTAL 3    NEW 1    PERSISTENT 0    RESOLVED 1    SKIP 0   │
│                                                             │
│   [FAIL]  1 new failures, 1 fixed, 1 passing                │
│                                                             │
│   New Failures:    json-1                                   │
│   Resolved Cases:  json-2                                   │
└─────────────────────────────────────────────────────────────┘
```

The core is deterministic: no LLM calls, no network calls, no hidden state.

## Get started

```bash
pip install entropy-loop-core
entropy-loop replay-demo
```

Or pin the current release and generate CI evidence plus the stability contract:

```bash
pip install entropy-loop-core==0.9.0
entropy-loop ci-demo    # write a local CI evidence bundle from a triage
entropy-loop contract   # print the deterministic v1 stability contract (JSON)
```

Works on Windows, macOS, and Linux with Python 3.10+.

<details>
<summary>Development setup</summary>

Use a virtual environment when working on the repository.

#### macOS / Linux

```bash
git clone https://github.com/koreaelonmusk/entropy-loop-core.git
cd entropy-loop-core
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
```

#### Windows PowerShell

```powershell
git clone https://github.com/koreaelonmusk/entropy-loop-core.git
cd entropy-loop-core
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e ".[dev]"
pytest
```

</details>

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
entropy-loop memory-demo   # compact repeated failure lessons with a MemoryPolicy
entropy-loop pack-demo     # build, save, load, and run a regression pack
entropy-loop agent-demo    # refresh a pack from an agent, then run it
entropy-loop triage-demo   # diff a baseline run against a current run
entropy-loop ci-demo       # write a CI evidence bundle from a triage
entropy-loop contract      # print the deterministic v1 stability contract (JSON)
entropy-loop demo          # run the loop: verify → trace → learn → retry → regress
entropy-loop doctor        # health-check the install
```

`memory-demo` shows how repeated failure lessons can be compacted with a
deterministic `MemoryPolicy` — see [docs/memory-policy.md](docs/memory-policy.md).

### Run a regression pack in CI

Turn captured failures into a portable pack and gate your build on it:

```bash
entropy-loop run-pack examples/json_agent_guard.pack.json
```

`run-pack` exits non-zero when a known agent regression reappears (0 = pass,
1 = failure, 2 = bad input), making replayable failure checks usable in CI. To
gate on your agent's *current* output, refresh the pack from an explicit local
command first (no shell, no secret injection):

```bash
entropy-loop refresh-pack input.pack.json output.pack.json -- python3 my_agent.py
entropy-loop run-pack output.pack.json
```

See [docs/regression-packs.md](docs/regression-packs.md),
[docs/agent-adapters.md](docs/agent-adapters.md), and
[docs/github-actions.md](docs/github-actions.md).

### Explain what changed

Don't just fail CI — diff the current run against a baseline and fail only on
newly introduced regressions:

```bash
entropy-loop compare-reports reports/baseline.json reports/current.json \
  --fail-on new-failures \
  --junit-report reports/entropy-loop-junit.xml \
  --html-report reports/entropy-loop.html
```

`compare-reports` classifies each case as newly failing, fixed, persistent, or
missing, and exits `1` only when the policy trips (0 = pass, 1 = policy fails,
2 = bad input). It can emit JSON, Markdown, JUnit XML, and a self-contained HTML
[Pixel Failure Console](docs/html-report.md) — see also
[docs/regression-triage.md](docs/regression-triage.md).

The console speaks English and Korean (`--html-locale en|ko`):

```bash
entropy-loop compare-reports examples/baseline_regression_report.json examples/current_regression_report.json \
  --fail-on new-failures \
  --html-report reports/entropy-loop-ko.html \
  --html-locale ko
```

## Use it in GitHub Actions

```yaml
- name: Compare Entropy Loop reports
  uses: koreaelonmusk/entropy-loop-core@v0.9.0
  with:
    baseline-report: baselines/entropy-loop.json
    current-report: reports/current.json
    fail-on: new-failures
    evidence-dir: reports/entropy-loop-evidence
    junit-report: reports/entropy-loop-junit.xml
    html-report: reports/entropy-loop.html
    html-locale: en
    write-step-summary: true
```

This writes a local CI evidence bundle and can append a summary to the GitHub
Actions step summary. The optional `junit-report` emits deterministic JUnit XML
for GitHub Actions, GitLab CI, Jenkins, CircleCI, and other test reporters;
`html-report` writes the self-contained [Pixel Failure Console](docs/html-report.md).
It does not call the GitHub API, comment on PRs, upload artifacts, or require
`GITHUB_TOKEN`. See [docs/ci-evidence.md](docs/ci-evidence.md).

## Stability contract

`entropy-loop contract` prints a deterministic JSON manifest of everything this
project keeps stable — public API, CLI commands, exit codes (`0` pass, `1` policy
fail, `2` usage/write error), the default evidence bundle files, report outputs,
and the GitHub Action boundary:

```bash
entropy-loop contract --output entropy-loop-contract.json
```

See [docs/stability-contract.md](docs/stability-contract.md).

When pinned to a semver tag (e.g. `@v0.8.0`) with no `package-version`, the Action
installs the matching PyPI version (`entropy-loop-core==0.8.0`). On a branch ref
like `main` it installs the latest; set `package-version` for reproducible CI.

## Output surfaces

One failure trace, read five ways — plus the contract that keeps them stable:

| Surface | Purpose |
|---|---|
| JSON | Machine-readable regression data |
| Markdown | Human-readable report |
| JUnit XML | CI-native test reporting |
| HTML Console | Visual [Pixel Failure Console](docs/html-report.md) |
| GitHub Action | CI evidence generation |
| Stability Contract | Stable behavior boundary |

All of these are written as local files. No telemetry, no hidden network calls.

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

## Haetae Guardian

<p align="center">
  <img src="docs/assets/haetae/haetae_clean.png" alt="Haetae guardian pixel mascot" width="180">
</p>

Haetae is the guardian mascot of Entropy Loop Core.

In this project, Haetae represents failure evidence, reliability boundaries, and
regression memory. It watches the loop, preserves the evidence, and protects the
reliability boundary — the mascot is a brand layer, never part of the core logic.

Entropy Loop does not claim to magically fix AI systems. It preserves failures as
evidence, turns them into repeatable checks, and makes regressions visible in CI.

> **한국어:** 해태는 실패 증거, 신뢰 경계, 회귀 기억을 지키는 Entropy Loop Core의
> 수호자입니다.

The mascot is derived from an original pixel-art source
([`docs/assets/haetae/haetae_original.json`](docs/assets/haetae/haetae_original.json),
preserved unmodified). All launch imagery lives locally under
[`docs/assets/haetae/`](docs/assets/haetae/) — no external CDN, no remote images.

## The loop

```text
AI agent failure
        ↓
Captured evidence
        ↓
Replayable regression case
        ↓
CI report
        ↓
Stable contract
```

## Boundaries

Entropy Loop Core is intentionally narrow.

**It does not**

- perform root-cause analysis,
- guarantee correctness,
- self-heal code,
- call external services by default,
- send telemetry,
- require hidden network access.

**It does**

- preserve failure evidence,
- generate regression artifacts,
- produce CI-readable outputs,
- expose stable behavior contracts,
- keep local, deterministic workflows.

> **Open-source the primitive, not the private advantage.** This repository
> contains only generic reliability primitives — no business logic, proprietary
> prompts, customer data, secrets, external AI API calls, or network calls. See
> [docs/public-private-boundary.md](docs/public-private-boundary.md).

## Releases

- **v0.9.0** — CI-native reporter outputs (JUnit XML) *(current)*
- **v0.8.1** — Action runner hardening (self-test)
- **v0.8.0** — GitHub Action / CI evidence bundle
- **v0.7.0** — regression triage / baseline diff
- **v0.6.0** — agent adapter / live pack refresh
- **v0.5.0** — regression packs / CI gate
- **v0.4.0** — memory policy / lesson compaction
- **v0.3.1** — packaging readiness
- **v0.3.0** — replay
- **v0.2.0** — classification + evaluation
- **v0.1.0** — the first Failure Compiler loop

Details in [CHANGELOG.md](CHANGELOG.md).

## Roadmap

- **Next (directional)** — persistence adapters, richer reports, and broader
  failure-memory recall.

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
