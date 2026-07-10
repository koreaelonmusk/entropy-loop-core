<p align="center">
  <img src="docs/assets/haetae/haetae_readme_hero.svg" alt="Entropy Loop Core Haetae guardian mascot and project vision" width="900">
</p>

<h1 align="center">Entropy Loop Core</h1>

<p align="center">
  <strong>AI agents fail in loops.</strong> Entropy Loop turns those failures into tests, CI evidence, JUnit reports, HTML failure consoles, and stable contracts.
</p>

<p align="center">
  <strong>한국어:</strong> Entropy Loop는 AI 에이전트 실패를 테스트, CI 증거, JUnit 리포트, 사람이 읽는 실패 콘솔, 안정성 계약으로 변환합니다.
</p>

<p align="center">
  <a href="https://pypi.org/project/entropy-loop-core/"><img src="https://img.shields.io/pypi/v/entropy-loop-core.svg" alt="PyPI"></a>
  <a href="https://github.com/koreaelonmusk/entropy-loop-core/actions/workflows/ci.yml"><img src="https://github.com/koreaelonmusk/entropy-loop-core/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License: Apache-2.0"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="#get-started">Get started</a> ·
  <a href="#the-loop">The loop</a> ·
  <a href="#output-surfaces">Outputs</a> ·
  <a href="#use-it-in-github-actions">GitHub Action</a> ·
  <a href="#stability-contract">Contract</a> ·
  <a href="#boundaries">Boundaries</a>
</p>

> Star the repo if you want to follow the Failure Compiler roadmap.

## What it does

Entropy Loop Core is a **Failure Compiler for AI agents**.

It verifies agent outputs, captures failed behavior, compiles failures into regression cases, replays them, and turns the result into CI-readable evidence.

The core is deterministic: no LLM calls, no network calls, no hidden state.

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

## Haetae Guardian

Haetae is the guardian mascot of Entropy Loop Core.

In this project, Haetae represents failure evidence, reliability boundaries, and regression memory.

Entropy Loop does not claim to magically fix AI systems. It preserves failures as evidence, turns them into repeatable checks, and makes regressions visible in CI.

해태는 실패 증거, 신뢰 경계, 회귀 기억을 지키는 Entropy Loop Core의 수호자입니다.

## Output surfaces

| Surface | Purpose |
|---|---|
| JSON | Machine-readable regression data |
| Markdown | Human-readable report |
| JUnit XML | CI-native test reporting |
| HTML Console | Visual failure console |
| GitHub Action | CI evidence generation |
| Stability Contract | Stable behavior boundary |

## Get started

```bash
pip install entropy-loop-core
entropy-loop replay-demo
entropy-loop contract
```

Works on Windows, macOS, and Linux with Python 3.10+.

## Example

Turn a failure into a regression case, then replay it against a fixed agent:

```python
from entropy_loop_core import AgentOutput, FailureTrace, RegressionRunner, RegressionSuite
from entropy_loop_core import RetryContext, Task, VerificationPolicy, Verifier, generate_regression_case

verifier = Verifier.from_policy(
    VerificationPolicy(require_non_empty=True, required_terms=["status"])
)

task = Task(id="job-1", instruction="report the job status")
bad = AgentOutput(content="done")

case = generate_regression_case(
    FailureTrace(task=task, output=bad, verification_result=verifier.verify(bad), attempt=1)
)

def fixed_agent(task: Task, ctx: RetryContext) -> AgentOutput:
    return AgentOutput(content="status: ok")

report = RegressionRunner().run_suite(
    RegressionSuite(name="job", cases=[case]), fixed_agent, verifier