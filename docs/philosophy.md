# Philosophy

## Failure is fuel, not garbage

Most AI agent frameworks showcase the happy path: task in, answer out, retry if
it breaks. But in production the money is burned on the *unhappy* path —
malformed tool calls, broken JSON, hallucinated answers, the same mistake made
over and over, retries that spiral into cost without ever getting smarter.

Logs pile up. Learning does not happen.

The gap is clear:

> **AI agents still have no black box and no mistake notebook.**

Entropy Loop Core exists to fill it.

## From retry library to Failure Compiler

A retry library does this:

```
Agent → Output → Retry
```

A Failure Compiler does this:

```
Agent → Output → Verify → Failure Trace → Lesson → Memory → Better Retry → Regression Test
```

The difference is that a failure is no longer discarded. It is **compiled** into
assets for future runs:

1. **Detect** bad outputs with explicit rules.
2. **Explain** why they failed, with a name and a severity.
3. **Store** the failure as a structured trace.
4. **Compile** the trace into a reusable lesson.
5. **Retry** with that lesson in context.
6. **Regress** — optionally emit a case so the same failure is checked forever.

## Why deterministic

The compiler itself uses **no LLM and no network**. Given the same failure it
always produces the same lesson and the same regression case. That makes the
reliability layer itself reliable: fully testable, reproducible, auditable, and
free of vendor lock-in. The intelligence you plug in lives in *your* agent — the
core just makes its failures productive.

## The bet

> **The real moat in AI is not generating the right answer.
> It is turning failure into an asset for the next run.**

Entropy Loop Core is a small, readable, open-source core for exactly that.
