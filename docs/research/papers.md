# Papers

A public-safe reading table grounding the design of Entropy Loop Core in prior
work. Every row summarizes a **publicly known** idea and the **generic** design
primitive it suggests for an open-source Failure Compiler. No private data,
benchmarks, prompts, or product internals appear here.

> For how deeply each paper is reflected in the current code, see
> [paper-primitive-matrix.md](paper-primitive-matrix.md).

> **Citation note:** titles and years are recorded as a maintainer reading list.
> Verify each citation against its primary source before using it in a formal
> publication. Where a year is marked `(verify)`, confirm the reference first.
> Publication safety of every row below is **PUBLIC_OK** — these are summaries of
> public research and generic primitives only.

| Paper | Year | Core public idea | Why it matters for Entropy Loop Core | Public design primitive derived | Risk / limitation | Impl. priority | Safety |
|---|---|---|---|---|---|---|---|
| ReAct: Synergizing Reasoning and Acting in Language Models | 2023 | Interleave reasoning traces with actions so an agent can plan and act step by step | Gives us a place to observe and verify each acting step, not just the final answer | `AgentOutput` as an observable step; `Verifier` boundary | Reasoning traces can be verbose and unreliable | v0.1 | PUBLIC_OK |
| Reflexion: Language Agents with Verbal Reinforcement Learning | 2023 | Store verbal self-feedback in memory to improve later trials — no weight updates | This is the heart of "failure as fuel": a failure becomes a reusable lesson | `FailureTrace` → `Lesson`; `MemoryStore` | Self-feedback quality varies; not a learning guarantee | v0.1 | PUBLIC_OK |
| Self-Refine: Iterative Refinement with Self-Feedback | 2023 | The same model critiques and revises its own output iteratively | Motivates a controlled retry loop with feedback between attempts | `RetryContext`; `LoopResult` | Can loop without converging; needs bounds | v0.1 | PUBLIC_OK |
| CRITIC: LLMs Can Self-Correct with Tool-Interactive Critiquing | 2023 | Use external tools to verify and correct outputs rather than trusting the model | Verification should be explicit and rule/tool-based, not vibes | `Verifier` with explicit rules | Tool availability and correctness are assumptions | v0.1 | PUBLIC_OK |
| Voyager: An Open-Ended Embodied Agent with LLMs | 2023 | Build a reusable skill library and an automatic curriculum over time | Lessons and regression cases accrete into durable, reusable knowledge | `Lesson` library; `RegressionCase` corpus | Skill/lesson reuse needs good retrieval | v0.2 | PUBLIC_OK |
| Generative Agents: Interactive Simulacra of Human Behavior | 2023 | A memory stream with retrieval, reflection, and relevance scoring | Motivates relevance-ranked lesson recall for retries | `MemoryStore.relevant_lessons`; `MemoryPolicy` | Retrieval heuristics can surface noise | v0.2 | PUBLIC_OK |
| Toolformer: Language Models Can Teach Themselves to Use Tools | 2023 | Models can learn when and how to call tools/APIs | Frames tool-call failures as a verifiable failure class | Tool-call verification rules | Out of scope for a deterministic core loop | later | PUBLIC_OK |
| SWE-agent: Agent-Computer Interfaces Enable Automated SWE | 2024 | A well-designed agent-computer interface strongly affects reliability | Clean, typed boundaries matter more than model cleverness | Typed contracts around `Task`/`AgentOutput` | Interface design is domain-specific | v0.2 | PUBLIC_OK |
| A-MEM: Agentic Memory for LLM Agents | 2025 (verify) | Dynamically organized, linked agent memory (Zettelkasten-style) | Suggests structured, linkable lessons rather than a flat log | `MemoryPolicy`; linked `Lesson`s | Added structure adds complexity; defer | later | PUBLIC_OK |
| Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory | 2025 (verify) | A scalable long-term memory layer for production agents | Motivates a pluggable persistence interface later | `MemoryStore` persistence interface | Scalability concerns are beyond the core | later | PUBLIC_OK |
| Agentic Memory: Unified Long-Term and Short-Term Memory Management | (verify) | Manage short- and long-term memory under one policy | Separates ephemeral retry context from durable lessons | `RetryContext` vs `MemoryStore` split | Policy tuning is workload-specific | later | PUBLIC_OK |
| Infini Memory: Maintainable Topic Documents for Long-Term Agent Memory | (verify) | Maintainable, topic-organized long-term memory documents | Motivates grouping lessons by topic/tag for recall | Lesson `tags`; topic grouping | Topic maintenance overhead | later | PUBLIC_OK |
| ReliabilityBench: Evaluating LLM Agent Reliability Under Perturbations and Tool Failures | (verify) | Evaluate agents under perturbations and tool failures | Regression cases are exactly this idea, scoped locally | `RegressionCase`; `EvaluationPolicy` | Benchmarks can overfit; keep generic | v0.3 | PUBLIC_OK |
| A Survey on Evaluation of LLM-based Agents | 2024 | Surveys how agent behavior and reliability are evaluated | Frames what "verification" and "regression" should measure | `EvaluationPolicy` (abstract) | Surveys date quickly | v0.3 | PUBLIC_OK |

## How to read this table

- **Core public idea** — a one-line, publicly known summary. Not a claim of
  novelty or correctness beyond what the paper states.
- **Public design primitive derived** — the generic, open-source abstraction the
  idea suggests. These map to `docs/research/design-primitives.md`.
- **Implementation priority** — a rough sequencing hint (`v0.1`, `v0.2`, `v0.3`,
  `later`), not a commitment.
- **Safety** — the publication classification from
  `docs/research/public-private-boundary.md`. Everything here is PUBLIC_OK.

Anything that would tie these ideas to a specific private product, dataset, or
prompt belongs in a private repository, not here.
