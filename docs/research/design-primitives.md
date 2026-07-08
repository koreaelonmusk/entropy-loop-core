# Design Primitives

This document maps public research ideas onto the open-source primitives of
Entropy Loop Core. Each primitive is a **generic abstraction** — a raw part —
not a business capability.

> **Boundary reminder:** open-source the primitive, not the private advantage.
> Commercial products may build private policies, datasets, dashboards, and
> deployment workflows on top of the open-source core. Those layers are out of
> scope for this repository. See `public-private-boundary.md`.

The canonical pipeline these primitives serve:

```txt
Task → AgentOutput → VerificationResult → FailureTrace → Lesson → Retry → LoopResult → RegressionCase
```

Publication safety for every primitive below is **PUBLIC_OK** unless noted.

---

## Task

- **What it means** — a unit of work for an agent: an instruction plus optional
  metadata.
- **Supporting papers** — ReAct (steps to act on), SWE-agent (clean task/interface
  boundaries).
- **When** — v0.1.
- **Minimal public implementation** — a small typed model (`id`, `instruction`,
  `metadata`).
- **What not to build yet** — task graphs, dependencies, schedulers.
- **Safety** — PUBLIC_OK.

## AgentOutput

- **What it means** — the raw output an agent produced for one attempt.
- **Supporting papers** — ReAct (observable steps), CRITIC (something to verify).
- **When** — v0.1.
- **Minimal public implementation** — `content` plus optional `metadata`.
- **What not to build yet** — multi-modal payloads, streaming buffers.
- **Safety** — PUBLIC_OK.

## VerificationResult

- **What it means** — the verdict of checking an output: pass/fail, reason, rule
  name, severity.
- **Supporting papers** — CRITIC (tool-interactive verification), Self-Refine
  (feedback signal).
- **When** — v0.1.
- **Minimal public implementation** — a typed record carrying the first failing
  rule.
- **What not to build yet** — scoring models, probabilistic confidences.
- **Safety** — PUBLIC_OK.

## FailureTrace

- **What it means** — a structured record of one failed attempt (task, output,
  verdict, attempt, timestamp).
- **Supporting papers** — Reflexion (failure as reusable signal).
- **When** — v0.1.
- **Minimal public implementation** — a typed bundle of the above fields.
- **What not to build yet** — distributed tracing, external log shipping.
- **Safety** — PUBLIC_OK. (Never store private data inside a trace.)

## Lesson

- **What it means** — a reusable takeaway compiled from a failure: summary, what
  to avoid, a recommended prompt patch, tags.
- **Supporting papers** — Reflexion (verbal feedback), Voyager (reusable skills).
- **When** — v0.1.
- **Minimal public implementation** — deterministic, rule-keyed generation from a
  `FailureTrace`.
- **What not to build yet** — LLM-written lessons, learned lesson ranking.
- **Safety** — PUBLIC_OK. (No proprietary prompt content in lessons.)

## MemoryStore

- **What it means** — storage for failures and lessons, with recall of relevant
  lessons for a task.
- **Supporting papers** — Generative Agents (memory stream + retrieval), Mem0,
  A-MEM (long-term memory).
- **When** — v0.1 (in-memory); persistence later.
- **Minimal public implementation** — in-memory lists plus keyword-overlap
  relevance.
- **What not to build yet** — vector databases, cloud sync, sharding.
- **Safety** — PUBLIC_OK. (Persistence backends must not embed private data.)

## RetryContext

- **What it means** — the ephemeral context handed to an agent on a retry
  (attempt number and relevant lessons).
- **Supporting papers** — Self-Refine (iterative refinement), Reflexion (feedback
  in the next trial).
- **When** — v0.1 (currently expressed as the agent context object).
- **Minimal public implementation** — task + attempt + lessons passed to the
  agent.
- **What not to build yet** — complex context-window budgeting strategies.
- **Safety** — PUBLIC_OK.

## LoopResult

- **What it means** — the structured outcome of a run: status, attempts, output,
  failures, lessons, regression cases.
- **Supporting papers** — Self-Refine (bounded iteration), the evaluation survey
  (what to report).
- **When** — v0.1.
- **Minimal public implementation** — a typed result aggregating the run.
- **What not to build yet** — analytics rollups, dashboards.
- **Safety** — PUBLIC_OK.

## RegressionCase

- **What it means** — a test-like artifact pinning a task and the rule that must
  pass for a past failure to count as fixed.
- **Supporting papers** — ReliabilityBench (perturbation/failure evaluation),
  Voyager (accreting durable knowledge).
- **When** — v0.1 (generation); export/replay workflow later.
- **Minimal public implementation** — name, instruction, expected rule, failure
  reason.
- **What not to build yet** — a full test-runner, private benchmark corpora.
- **Safety** — PUBLIC_OK. (Regression corpora with private data stay private.)

## Verifier

- **What it means** — applies ordered, composable rules to an output and returns
  the first violation.
- **Supporting papers** — CRITIC, Self-Refine.
- **When** — v0.1.
- **Minimal public implementation** — a list of `Callable` rules; built-ins for
  non-empty, required terms, JSON, length.
- **What not to build yet** — model-based judges as a default.
- **Safety** — PUBLIC_OK.

## LessonGenerator

- **What it means** — compiles a `FailureTrace` into a `Lesson`, deterministically.
- **Supporting papers** — Reflexion.
- **When** — v0.1.
- **Minimal public implementation** — fixed per-rule guidance templates; no LLM,
  no network, no randomness.
- **What not to build yet** — LLM-driven lesson synthesis (keep the core
  deterministic).
- **Safety** — PUBLIC_OK.

## MemoryPolicy

- **What it means** — a strategy for what to remember, how to rank it, and when to
  forget.
- **Supporting papers** — Generative Agents (relevance/recency/importance), A-MEM,
  Agentic Memory (unified short/long-term), Infini Memory (topic organization).
- **When** — v0.2+ (start with a single simple default; make it pluggable later).
- **Minimal public implementation** — an interface with a keyword-overlap default.
- **What not to build yet** — many competing policies before a real use case.
- **Safety** — PUBLIC_OK. Domain-specific policies may be built privately on top
  (PUBLIC_ABSTRACT_ONLY for anything commercial).

## EvaluationPolicy

- **What it means** — how success, reliability, and regression are measured.
- **Supporting papers** — A Survey on Evaluation of LLM-based Agents,
  ReliabilityBench.
- **When** — v0.3 (abstract interface first).
- **Minimal public implementation** — a generic interface; concrete metrics kept
  simple and public.
- **What not to build yet** — industry-specific evaluation datasets (those are
  PUBLIC_ABSTRACT_ONLY and stay private).
- **Safety** — PUBLIC_OK for the interface; private datasets are
  PRIVATE_DO_NOT_PUBLISH.

---

## What stays out of the open-source core

Only in generic, abstract language (PUBLIC_ABSTRACT_ONLY): future enterprise
integrations, production feedback loops, domain-specific reliability policies,
private deployment options, commercial dashboards, and industry-specific
evaluation data. Their internals are PRIVATE_DO_NOT_PUBLISH and never appear
here.
