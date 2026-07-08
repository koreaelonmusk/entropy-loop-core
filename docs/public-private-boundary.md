# Public / Private Boundary

This repository is **public open-source software**. This document is the rule for
what may live here and what must not.

> **Open-source the primitive, not the private advantage.**

## 1. What is safe to publish

- Generic AI-agent reliability primitives (verification, retry, memory,
  lessons, regression cases).
- Public research-inspired concepts and citations.
- Simple in-memory failure storage.
- Basic deterministic verification rules.
- Basic, deterministic lesson generation.
- A simple retry loop and a fake demo agent.
- Generic examples, tests, and docs for open-source maintainers.

## 2. What must remain private

Never include, in any form:

- Private or business-specific logic and QA data.
- Proprietary internal architecture and system design.
- Customer data or user logs.
- Private or proprietary prompts.
- Proprietary algorithms or internal operating playbooks.
- Real production failure patterns or private benchmarks.
- Cloud sync, auth, billing, dashboards, or enterprise features.
- Domain-specific commercial policies.
- Secrets or API keys.
- External network calls or external AI API calls.

## 3. What can be discussed only abstractly

The following may be mentioned **only** in generic terms, with no implementation
detail, internal names, or data:

- future enterprise integrations,
- production feedback loops,
- domain-specific reliability policies,
- private deployment options,
- commercial dashboards,
- industry-specific evaluation data.

The one allowed framing for the commercial layer:

> "Commercial products may build private policies, datasets, dashboards, and
> deployment workflows on top of the open-source core."

## 4. Examples of allowed wording

- "The core exposes a `Verifier`; domain policies can be layered privately on
  top."
- "A regression case pins a task and the rule that must pass, so a failure can be
  checked over time."
- "Lessons are compiled deterministically from failure traces — no model calls."

## 5. Examples of forbidden wording

- "Our internal QA dataset shows ..." (private benchmark).
- "The production prompt we use for X is ..." (proprietary prompt).
- "Customer <name> hit this failure ..." (customer data).
- Any concrete description of how a private product works internally.

## The rule

> **If a detail comes from private product operations, customer data,
> proprietary workflows, or unreleased strategy, it does not belong in this
> repository.**

When uncertain, treat it as private and leave it out.
