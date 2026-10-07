# ==============================================================================
# FIRST-PRINCIPLES VERCEL ZERO-REMOTE-BUILD POLICY v2
# Target: https://github.com/koreaelonmusk/*
# ==============================================================================

[OBJECTIVE]
Minimize Vercel build spend by deleting unnecessary remote-build paths without weakening correctness.
Never claim "$0" or "fully enforced" unless the repository and Vercel project settings have been verified.

[ENGINEERING ALGORITHM]
1. Question every requirement.
2. Delete unnecessary parts/processes.
3. Simplify and optimize.
4. Accelerate cycle time.
5. Automate only after the first four steps.

### LAW 1. DISABLE GIT-TRIGGERED VERCEL BUILDS
- Root `vercel.json` MUST set:
  {
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "git": { "deploymentEnabled": false }
  }
- Preserve all existing routes, rewrites, functions, headers, crons, framework and security settings when adding this key.
- If project settings expose an Ignored Build Step, use `exit 0` so every accidental Git deployment is skipped.
- Do NOT use a condition that returns non-zero for production; Vercel interprets non-zero as "continue the build".

### LAW 2. NO UNVERIFIED REMOTE-BUILD CLI PATH
- Repository-owned deployment scripts/CI MUST NOT call bare `vercel`, `vercel deploy`, or `vercel --prod` when those commands would trigger a remote build.
- Preferred compatible flow:
  `vercel pull --yes --environment=production && <required local checks> && vercel build --prod && vercel deploy --prebuilt --prod`
- `--prebuilt` is allowed ONLY after checking compatibility. Vercel System Environment Variables are not automatically available at prebuilt build time, and features such as Skew Protection can require additional configuration.
- If a project depends on unavailable build-time Vercel system variables and no safe explicit binding exists, HOLD deployment rather than silently shipping a broken artifact.
- If the repository has no machine-owned deployment entrypoint, treat the CLI ban as an agent/human policy, not as a claim that the repository technically prevents manual CLI use.

### LAW 3. NEVER BUY COST SAVINGS WITH BROKEN BUILDS
- Do NOT globally set `typescript.ignoreBuildErrors=true` or `eslint.ignoreDuringBuilds=true` merely to shorten builds.
- Type checking, linting, tests and security checks MUST run locally or in required CI before a production artifact is accepted.
- Suppression inside a framework build is permitted only when equivalent independent required checks exist and the exact deployment commit has passed them.
- Do not generate huge static page loops when on-demand, dynamic rendering, ISR, or affected-only builds are correct alternatives.

### LAW 4. PROJECT RESOURCE FLOOR
- When Vercel project settings are writable, prefer:
  - buildMachineType: basic
  - buildMachineSelection: fixed
  - previewDeploymentsDisabled: true when previews are not required
  - Ignored Build Step: `exit 0`
- Do not pause a production project merely to imitate Spend Management.
- Do not mutate budget/concurrency controls unless the exact supported API/setting and account permissions are verified.

### LAW 5. VERIFICATION BEFORE CLAIMS
For CI/CD or deployment changes:
1. inspect the repository's actual deploy entrypoints;
2. verify `vercel.json` preserves existing configuration and disables Git deployments;
3. verify local/CI correctness gates still fail closed;
4. inspect Vercel project settings when accessible;
5. report unsupported or permission-blocked controls explicitly.


---

# CLAUDE.md

Project-level guidance for Claude Code working in this repository. Read this
before any implementation work. These rules take precedence over general habits.

## 1. Project Mission

**Entropy Loop Core is an open-source Failure Compiler for AI agents.** It turns
bad AI agent outputs into structured failure traces, lessons, retries, and
regression cases.

This repository is a **minimal, open-source reliability layer** for AI agents.
Its entire job is to make agent *failures* productive:

- verify outputs against explicit rules,
- capture each failure as a structured trace,
- compile traces into reusable lessons,
- retry with those lessons in context,
- generate regression cases so the same failure does not return.

Keep the scope tight. This is a reliability core, not a framework, not a product.

## 2. Non-Negotiable Boundaries

Claude must **never** add any of the following to this repository:

- private or business-specific logic
- proprietary product internals
- private or proprietary prompts
- customer data
- enterprise dashboard code
- cloud sync
- billing
- auth
- proprietary algorithms
- hidden secrets or credentials
- network calls — unless the user explicitly requests them
- external AI API calls — unless the user explicitly requests them

If a task seems to require any of these, stop and ask instead of proceeding.

## 3. Design Philosophy

Apply, in order of priority:

- **Andrej Karpathy-style simplicity** — the code should read like an
  explanation of the idea.
- **Ponytail anti-overengineering principle** — solve the problem in front of
  you, not the imagined future one.
- small, readable files
- boring, explicit code over clever code
- minimal abstractions; introduce one only when duplication demands it
- no speculative framework design
- no plugin architecture until a real use case exists
- one clear loop before many features

When two designs work, choose the one with fewer moving parts.

## 4. Work Discipline

**Before coding**, Claude must:

- inspect the repository and read the relevant files
- summarize the current state in a sentence or two
- identify the *smallest useful change* that moves the task forward
- ask only when genuinely blocked; otherwise pick the obvious default
- avoid unrelated refactors
- define the validation steps up front

**After coding**, Claude must:

- run the tests if a test suite is available (`pytest`)
- run linting if configured (`ruff check .`, `ruff format .`)
- summarize which files changed and why
- list any known limitations or follow-ups
- **not push** unless the user explicitly instructs it

## 5. Open Source Strategy

- This repository is **public open-source software**.
- The core interfaces and the minimal loop are meant to be open.
- Business assets, proprietary logic, and product code stay **private** and out
  of this repository.
- The project is licensed **Apache-2.0**; respect it in headers, contributions,
  and dependencies.
- The goal is **ecosystem trust** — a small, honest, readable core — not dumping
  private product code into the open.

## 6. Coding Standards

Use:

- Python 3.10+
- `pydantic` for typed models (when models are needed)
- `typer` for the CLI (when a CLI is needed)
- `pytest` for tests
- `ruff` for linting and formatting
- docstrings on all public classes and functions

Avoid:

- large or heavyweight dependencies
- global mutable state, unless it is intentionally simple and local
- hidden magic and implicit behavior
- unclear names
- premature optimization
- excessive inheritance (prefer plain functions and small classes)

## 7. Failure Compiler Model

Preserve this vocabulary and pipeline throughout the repository:

```txt
Task
  → AgentOutput
  → VerificationResult
  → FailureTrace
  → Lesson
  → Retry
  → LoopResult
  → RegressionCase
```

These are the canonical names. Do not rename or fork this vocabulary without an
explicit request. New work should slot into this pipeline rather than inventing a
parallel one.

The compiler stages (lesson and regression generation) must stay
**deterministic** — no LLM calls, no network, no randomness — so the reliability
layer is itself reliable and testable.

## 8. Commit Rules

- Prefer small, focused commits.
- Write clear, conventional commit messages, for example:
  - `docs: add claude project rules`
  - `feat: add minimal failure trace model`
  - `test: cover verifier rules`
- **Do not push** unless the user explicitly approves.
