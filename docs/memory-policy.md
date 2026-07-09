# Memory policy

Generating a lesson for every failure is useful — until it isn't. Left
unbounded, failure memory fills with near-duplicate lessons: the same missing
field, the same broken JSON, over and over. That noise makes the useful lessons
harder to find and slower to reuse.

`MemoryPolicy` and `LessonCompactor` add **deterministic failure-memory
hygiene**: keep the lessons that matter, merge the duplicates, and drop the rest.

## What it does

`LessonCompactor.compact(lessons, policy)` applies a `MemoryPolicy` and returns a
`CompactionResult`. In order, it can:

- **drop empty lessons** — lessons with no summary, guidance, or patch,
- **enforce `min_occurrences`** — drop lessons whose guidance appeared fewer than
  N times,
- **dedupe by fingerprint** — collapse lessons that give the same guidance (a
  fingerprint of the avoidance text, prompt patch, and tags — deliberately not
  the summary, which varies per occurrence),
- **dedupe by failure category** — collapse to one lesson per category,
- **cap per category** — keep at most N lessons per category,
- **cap total** — keep at most `max_lessons`, preferring (optionally) categories
  that have a regression case, then newest or oldest per `keep_latest`.

The result carries counts (`input_count`, `output_count`, `dropped_count`,
`merged_count`), a `dropped_reasons` breakdown, `category_counts`, and a
deterministic one-line `summary`.

## Compaction, not summarization

The summary is a fixed template — for example:

```text
Compacted 5 lesson(s) to 3; dropped 2 (2 duplicate(s)).
```

It is **not** written by a model. Given the same lessons and policy, compaction
always produces the same output.

## What it does not do

- No LLM calls and no model-written summaries.
- No network calls and no external services.
- No vector store, no embeddings, no database.
- No hidden or background persistence — `save_lesson_memory` /
  `load_lesson_memory` use only explicit local paths you provide.
- No model training and no "self-improving" behavior. This is memory hygiene,
  not learning.

## Try it

```bash
entropy-loop memory-demo
```

A worked example is in
[examples/memory_policy_guard.py](../examples/memory_policy_guard.py).
