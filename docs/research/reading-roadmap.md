# Reading Roadmap

A 7-day, public-safe reading plan for contributors who want to ground Entropy
Loop Core in prior work. Each day pairs two papers and ends with concrete,
open-source takeaways. Nothing here references private products, data, or
strategy.

> Read for **primitives**, not for a private moat. The combinations, datasets,
> and operational loops a business builds on top stay private.

Full citations and the safety classification for each paper are in
`papers.md`. The boundary rules are in `public-private-boundary.md`.

---

## Day 1 — ReAct + Reflexion

**Focus:** observable reasoning/acting steps, and turning failures into verbal
lessons stored in memory.

- **Public engineering takeaways**
  1. Make every acting step observable so it can be verified, not just the final
     answer.
  2. A failure can improve the next attempt without any weight update.
  3. Memory of past attempts is a first-class input to the next attempt.
- **Add to CLAUDE.md:** reinforce "failure is data" — traces feed lessons.
- **Avoid overbuilding:** don't build a reasoning-trace framework; keep
  `AgentOutput` a plain observed step.
- **Publication safety note:** summaries of both papers are PUBLIC_OK; keep any
  example prompts generic.

## Day 2 — Self-Refine + CRITIC

**Focus:** iterative self-feedback, and explicit tool/rule-based verification.

- **Public engineering takeaways**
  1. Refinement needs an explicit feedback signal between attempts.
  2. Verification should be explicit (rules/tools), not implicit trust.
  3. Bounded iteration matters — loops need a stop condition.
- **Add to CLAUDE.md:** verification must be explicit and rule-based; retries must
  be bounded.
- **Avoid overbuilding:** don't default to a model-as-judge; start with simple
  deterministic rules.
- **Publication safety note:** keep verification rules generic; no private QA
  checks.

## Day 3 — Voyager + Generative Agents

**Focus:** reusable skill/lesson libraries, and memory streams with relevance
retrieval.

- **Public engineering takeaways**
  1. Lessons and regression cases should accrete into durable, reusable knowledge.
  2. Recall should be relevance-ranked, not a flat dump.
  3. Reflection over memory can compress many events into a few useful items.
- **Add to CLAUDE.md:** lessons are reusable assets; recall is relevance-based.
- **Avoid overbuilding:** don't add vector search yet; a keyword-overlap default
  is enough.
- **Publication safety note:** memory design is PUBLIC_OK; stored contents must
  never include private data.

## Day 4 — Toolformer + SWE-agent

**Focus:** learning tool use, and how the agent-computer interface shapes
reliability.

- **Public engineering takeaways**
  1. Tool-call failures are a distinct, verifiable failure class.
  2. Clean typed boundaries improve reliability more than model cleverness.
  3. Interface design is a reliability lever, not an afterthought.
- **Add to CLAUDE.md:** typed boundaries at every hand-off; treat tool failures as
  first-class traces.
- **Avoid overbuilding:** don't build a general tool framework in the core.
- **Publication safety note:** keep interface examples generic; no proprietary
  tool integrations.

## Day 5 — A-MEM + Mem0

**Focus:** structured, scalable long-term agent memory.

- **Public engineering takeaways**
  1. Long-term memory benefits from structure and links, not just append-only
     logs.
  2. Production memory needs a clean persistence interface.
  3. Separate the memory interface from its backend.
- **Add to CLAUDE.md:** keep `MemoryStore` an interface so backends can change.
- **Avoid overbuilding:** don't add persistence/cloud sync before a real use case
  (cloud sync internals are PRIVATE_DO_NOT_PUBLISH anyway).
- **Publication safety note:** the interface is PUBLIC_OK; any specific hosted
  backend design stays private.

## Day 6 — Agentic Memory + Infini Memory

**Focus:** unified short/long-term memory management and topic-organized memory.

- **Public engineering takeaways**
  1. Distinguish ephemeral retry context from durable lessons.
  2. Grouping lessons by topic/tag improves recall.
  3. Memory maintenance (merge, expire) is a policy, not a hardcoded rule.
- **Add to CLAUDE.md:** separate `RetryContext` from `MemoryStore`; make policies
  pluggable, not baked in.
- **Avoid overbuilding:** don't ship multiple memory policies before one is
  proven.
- **Publication safety note:** policy interfaces are PUBLIC_OK; tuned commercial
  policies are PUBLIC_ABSTRACT_ONLY.

## Day 7 — ReliabilityBench + A Survey on Evaluation of LLM-based Agents

**Focus:** evaluating reliability under perturbation and tool failure, and how
agent evaluation is framed.

- **Public engineering takeaways**
  1. Regression cases are local, reusable reliability checks.
  2. Define clearly what verification and regression should measure.
  3. Evaluation is a policy that should stay generic in the open core.
- **Add to CLAUDE.md:** regression is institutional memory; keep evaluation
  generic.
- **Avoid overbuilding:** don't build a benchmarking product; generate simple
  local regression cases.
- **Publication safety note:** the `EvaluationPolicy` interface is PUBLIC_OK;
  industry-specific evaluation datasets are PRIVATE_DO_NOT_PUBLISH.

---

## After the week

You should be able to justify every primitive in `design-primitives.md` from a
public source, and to state — for each — what the open core should *not* build
yet. If a takeaway feels like a commercial advantage rather than a primitive, it
belongs in a private repository, not here.
