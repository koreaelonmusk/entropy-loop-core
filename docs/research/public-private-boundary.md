# Public / Private Boundary

This document is the publication policy for everything under `docs/research/`
and, more broadly, for this open-source repository. It exists so that
paper-grounded design work never leaks commercial advantage.

> **Guiding principle: open-source the primitive, not the private advantage.**

Universal ideas that come from public research are safe to publish. The
combinations, datasets, operational loops, and customer-problem patterns that a
business builds on top of those primitives are not.

Every idea must be classified before it is written down:

- **PUBLIC_OK** — safe to publish here.
- **PRIVATE_DO_NOT_PUBLISH** — must never appear in this repository.
- **PUBLIC_ABSTRACT_ONLY** — may be referenced only in generic, abstract terms.

When in doubt, treat an idea as **PRIVATE_DO_NOT_PUBLISH**.

---

## 1. What is safe to publish

- Summaries of public academic papers and their citations.
- General open-source design principles.
- Generic AI-agent reliability concepts: verification, retry, memory,
  regression testing, self-reflection.
- Non-proprietary abstractions and interface shapes.
- General architecture diagrams of the open-source core.
- The Failure Compiler vocabulary already used in this repository
  (`Task → AgentOutput → VerificationResult → FailureTrace → Lesson → Retry →
  LoopResult → RegressionCase`).
- Minimal, illustrative implementation sketches of the open primitives.

## 2. What must remain private

None of the following may appear in this repository, in any form:

- private business logic or private QA data.
- proprietary system internal architecture.
- proprietary private system design.
- Proprietary or unreleased prompts.
- Customer data or user-specific information.
- Private logs or private benchmarks.
- Unreleased product strategy or private roadmap details.
- Enterprise dashboard logic.
- Cloud sync design.
- Billing or auth logic.
- Internal operational playbooks or private workflows.
- Anything that creates business risk if copied.

## 3. What can be discussed only abstractly

The following may be mentioned **only** in generic form, with no implementation
detail, no internal names, and no data:

- "future enterprise integrations"
- "production feedback loops"
- "domain-specific reliability policies"
- "private deployment options"
- "commercial dashboard"
- "industry-specific evaluation data"

The allowed framing for the commercial layer is exactly this generic sentence:

> "Commercial products may build private policies, datasets, dashboards, and
> deployment workflows on top of the open-source core."

## 4. Examples of allowed wording

- "Reflexion shows that verbal self-feedback stored in memory can improve later
  attempts without updating model weights."
- "The open-source core exposes a `Verifier` interface; policies for specific
  domains can be layered privately on top."
- "A regression case pins a task and the rule that must pass, so a failure can be
  checked over time."
- "Commercial products may build private policies, datasets, and dashboards on
  top of this core."

## 5. Examples of forbidden wording

- Any sentence naming a specific private product's internal component.
- "Our internal QA dataset shows that ..." (private benchmark).
- "The production prompt we use for X is ..." (proprietary prompt).
- "Customer <name> hit this failure when ..." (customer data).
- "The private roadmap for Q<n> is ..." (unreleased strategy).
- Any concrete description of how a private product works internally.

## 6. Rule of thumb for future contributors

Before adding anything, ask:

1. **Did this idea come from a public paper or a widely known open concept?**
   If yes, it is likely PUBLIC_OK.
2. **Would a competitor gain a real advantage by copying this?**
   If yes, it is PRIVATE_DO_NOT_PUBLISH.
3. **Is it a business capability rather than a primitive?**
   If yes, mention it only as PUBLIC_ABSTRACT_ONLY, or not at all.
4. **Am I unsure?**
   Then it is PRIVATE_DO_NOT_PUBLISH by default.

Keep these documents useful to open-source maintainers without exposing
commercial advantage. Every file here must be safe to publish on GitHub.
