# Paper → Primitive Matrix

This document maps public research to the concrete primitives in Entropy Loop
Core, and — honestly — how *deeply* each idea is currently reflected in the code.
The point is not to name-drop papers; it is to show which public ideas have been
**compressed into working primitives** and which are still ahead on the roadmap.

This is a **first-pass compression**: the Reflexion / Self-Refine / verification
family is in the core; the long-term-memory and tool-use families are not yet.

> Reflection degree is a self-assessment of how much of a paper's public idea is
> expressed in code today — `high`, `medium`, or `low` — not a claim about the
> paper or a benchmark result. Citations and safety classifications live in
> [papers.md](papers.md); the primitives themselves in
> [design-primitives.md](design-primitives.md).

## Strongly reflected today

These public ideas are expressed directly in v0.2.0 primitives.

| Paper / idea | Public idea (one line) | Reflected as | Degree |
|---|---|---|---|
| **Reflexion** | Store verbal self-feedback in memory to improve later trials (no weight updates) | `FailureTrace → Lesson → RetryContext` | high |
| **Self-Refine** | Iteratively critique and revise output with feedback between attempts | `Verifier → LessonGenerator → retry loop` | high |
| **ReAct** | Interleave reasoning and acting as observable steps | `Task → AgentOutput → VerificationResult → retry` | medium |
| **CRITIC** | Verify and correct outputs with explicit, tool-interactive checks | `Verifier`, `VerificationPolicy` | medium |
| **ReliabilityBench-style evaluation** | Evaluate reliability under failures; make failures measurable | `FailureCategory`, `EvaluationSummary`, `RegressionCase` | medium |

## Weakly reflected today (future work)

These public ideas inform the direction but are **not** meaningfully in the code
yet. They are deliberately deferred so the core stays small and sharp.

| Paper / idea | Public idea (one line) | What is missing | Likely home |
|---|---|---|---|
| **Voyager** | Accrete reusable skills into a growing library | Failures/lessons do not yet accumulate into a reusable, retrievable library | future |
| **Generative Agents** | Memory stream with retrieval, reflection, planning | No reflection or planning over a memory stream; recall is simple | v0.4.0 memory policy |
| **Toolformer** | Learn when and how to call tools | No tool-use decisions or tool-call verification | future |
| **SWE-agent** | A good agent-computer interface drives reliability | The repeatable task/interface loop is thin | v0.3.0 regression runner |
| **Mem0 / A-MEM / Agentic Memory / Infini Memory** | Structured, scalable long-term memory | Memory is simple in-memory keyword overlap | v0.4.0 memory policy |

## Reflection status, at a glance

```txt
ReAct                → Task / AgentOutput / verification / retry flow
Reflexion            → FailureTrace / Lesson / RetryContext
Self-Refine          → verification / LessonGenerator / retry loop
CRITIC               → Verifier / VerificationPolicy
ReliabilityBench     → FailureCategory / EvaluationSummary / RegressionCase
Voyager              → weak today; future skill/lesson library
Generative Agents    → weak today; future memory stream / reflection
Toolformer           → weak today; future tool-call verification
SWE-agent            → weak today; future regression runner / CLI workflow
Mem0 / A-MEM / …     → weak today; future MemoryPolicy
```

## Where this is heading

The next compression steps keep the identity — **a Failure Compiler for AI
agents** — and deepen it rather than widening into a general agent framework:

- **v0.3.0 — replay.** Turn generated `RegressionCase`s into a runnable suite so
  a remembered failure can be *replayed* and checked, not just stored. Theme:
  *"failures should not only be remembered — they should be replayed."*
- **v0.4.0 — memory policy.** Decide what to remember, group, and forget:
  deduplication, fingerprint grouping, and recent / relevant / frequent recall.

See [roadmap.md](../roadmap.md) for the conservative plan.

## Public-safety note

Everything here is PUBLIC_OK: summaries of public research and generic
primitives. Commercial products may build private policies, datasets,
dashboards, and deployment workflows on top of the open-source core — those, and
any private data, benchmarks, or workflows, stay out of this repository. See
[public-private-boundary.md](public-private-boundary.md).
