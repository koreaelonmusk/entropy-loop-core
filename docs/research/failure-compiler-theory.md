# Failure Compiler Theory

The public thesis behind Entropy Loop Core. It is intentionally generic and
open-source: it makes no proprietary claims and reveals no private strategy.

> **Thesis:** Entropy Loop Core is a Failure Compiler for AI agents. It converts
> failed outputs into structured traces, reusable lessons, retry context, and
> regression cases.

A retry library discards failure. A **Failure Compiler** treats failure as
input and compiles it into durable assets for future runs. The pipeline:

```txt
Task → AgentOutput → VerificationResult → FailureTrace → Lesson → Retry → LoopResult → RegressionCase
```

The thesis rests on five plain, well-supported ideas. None of them requires
model training or weight updates, and the core does not perform any.

---

## 1. Failure as data

A failed output is not noise to be thrown away; it is a structured observation.
Capturing *what* was attempted, *what* came back, and *why* it was rejected turns
an anecdote into a record you can reason about. This mirrors the public idea
(ReAct, Reflexion) that an agent's steps and mistakes are first-class signals,
not just its final answer.

In the core, this is the `FailureTrace`.

## 2. Memory as compressed experience

Raw failures pile up quickly. A `Lesson` is a compressed, reusable form of one
or more failures: what to avoid and what to do instead. Public work on agent
memory (Generative Agents, Voyager, and later long-term memory work) supports the
idea that agents improve when experience is stored, compressed, and recalled by
relevance rather than replayed in full.

In the core, this is the `Lesson` plus `MemoryStore`, with relevance-based
recall. The compilation from trace to lesson is **deterministic** — no LLM, no
network — so the memory layer is itself testable and reproducible.

## 3. Verification as boundary

Improvement is only meaningful against an explicit standard. Verification draws a
boundary between acceptable and unacceptable output using named, composable
rules. Public work (CRITIC, Self-Refine) supports making the check explicit —
tool- or rule-based — rather than trusting the model to self-assess implicitly.

In the core, this is the `Verifier` and `VerificationResult`. Every failure is
attributed to a specific rule, which is what makes it compilable.

## 4. Retry as controlled adaptation

A retry is not a blind re-roll. It is a *controlled* adaptation: the next attempt
runs with the lessons from prior failures in its context, under a bounded number
of attempts. Public work on iterative refinement (Self-Refine, Reflexion) shows
that feeding structured feedback into the next attempt can help — while unbounded
loops are a known hazard, so bounds are mandatory.

In the core, this is the `RetryContext` carried into each attempt, and the
bounded loop that produces a `LoopResult`.

## 5. Regression as institutional memory

Once a failure is understood, it should never quietly return. A `RegressionCase`
pins a task and the rule that must pass for the failure to count as fixed —
turning a one-time fix into a durable check. Public reliability-evaluation work
(perturbation/tool-failure evaluation, agent-evaluation surveys) supports treating
past failures as reusable reliability checks.

In the core, this is the `RegressionCase`, generated from a trace.

---

## What this thesis deliberately does not claim

- **No training claims.** The core does not train models or update weights. All
  adaptation happens through explicit context (lessons), not learning.
- **No guarantees.** Verification and lessons improve the odds; they do not
  promise correctness. Rules are only as good as the rules you write.
- **No private strategy.** How a commercial product composes these primitives —
  its policies, datasets, dashboards, and deployment workflows — is out of scope
  for this repository and stays private.

## Why keep it public

The primitives above are universal and come from public research. Publishing them
builds ecosystem trust and invites contribution. The private advantage is never a
single primitive — it is the *combination*: the data, the operational loops, and
the domain-specific patterns built on top. Those are exactly what this repository
leaves out.

> Open-source the primitive, not the private advantage.
