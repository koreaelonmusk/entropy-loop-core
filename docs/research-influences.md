# Research Influences

Entropy Loop Core is grounded in public research on agent reliability. This page
describes, at a high level, how public ideas *inspired* the open-source
architecture. It is intentionally light: it maps abstract themes to primitives,
not a detailed strategy.

> Detailed strategic research mapping is intentionally kept outside the public
> repository.

We do **not** claim to implement any paper in full. The wording below is
deliberate: "inspired by", "related to", "partially reflected in", and "future
direction". This project **captures, classifies, and summarizes** failures; it
does not train models or guarantee correctness.

| Research theme | Public idea | Entropy Loop Core primitive | Current status | Notes |
|---|---|---|---|---|
| Reasoning + acting | Treat an agent's steps as observable, checkable actions | `Task`, `AgentOutput`, `VerificationResult` | partially reflected | We observe and verify a step, not multi-step reasoning traces. |
| Verbal feedback / reflection | Store feedback from a failure to improve later attempts (no weight updates) | `FailureTrace`, `Lesson`, `RetryContext` | reflected | The heart of the loop; feedback is explicit, deterministic. |
| Self-refinement | Iterate with feedback between attempts | `LessonGenerator`, the retry loop | reflected | Bounded retries; no unbounded self-refinement. |
| Tool-assisted critique | Verify and correct outputs with explicit checks | `Verifier`, `VerificationPolicy` | reflected | Rule-based verification; no model-as-judge by default. |
| Agent memory | Remember and recall relevant past experience | `MemoryStore`, `RetryContext` | partially reflected | Simple in-memory recall today; richer policies are a future direction. |
| Software agent evaluation | Summarize how an agent performed | `EvaluationSummary` | partially reflected | A compact per-run rollup, not a benchmark suite. |
| Reliability under perturbation | Evaluate behavior when things go wrong | `FailureCategory`, `RegressionCase` | partially reflected | Failures are classified and pinned; broad perturbation testing is future work. |
| Regression testing | Turn a past failure into a repeatable check | `RegressionCase` | reflected (generation) | Replaying cases as a suite is a future direction. |

## Scope of this document

- **Included:** public paper themes, general concepts, and the generic
  primitives they inspired.
- **Excluded (by design):** detailed paper-by-paper build strategy, product
  roadmap specifics, and any private interpretation of how these ideas connect to
  applications beyond this open-source core.

For the primitives themselves, see [architecture.md](architecture.md) and
[reliability-model.md](reliability-model.md).
