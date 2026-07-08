# Recording the demo

A recorded GIF lives at [`docs/assets/demo.gif`](assets/demo.gif) and is shown in
the README. This page explains how to (re)generate it from the real CLI.

There are two tape scripts:

- [`demo.hero.tape`](../demo.hero.tape) — the **README hero GIF**: a short,
  cinematic take on `entropy-loop replay-demo` (narrative frame, then the real
  command and its result). This is what renders `docs/assets/demo.gif`.
- [`demo.tape`](../demo.tape) — a plain, lower-level recording of
  `entropy-loop demo` + `doctor`.

## What the demo shows

`entropy-loop demo` runs a fake agent that fails once (a required term is
missing), then compiles the failure into a lesson, retries with that lesson in
context, and succeeds — printing the category, fingerprint, an evaluation
summary, and a generated regression case.

Static output for reference:

```text
Entropy Loop Demo
1. Task started: 'report the job status'
2. Attempt 1 failed: missing required terms: ['status']
3. Failure category: missing_required_term
4. Failure fingerprint: fd46a1fcda19a179
5. Lesson generated
6. Retry context updated
7. Attempt 2 passed
8. Evaluation summary: status=success, attempts=2, failures=1, categories={'missing_required_term': 1}
9. Regression case generated: regression_report_the_job_status_contains_required_terms
```

## Record with VHS

[VHS](https://github.com/charmbracelet/vhs) turns a small script into a GIF.

```bash
brew install vhs          # or: go install github.com/charmbracelet/vhs@latest
pip install -e ".[dev]"   # so `entropy-loop` is on PATH
vhs demo.hero.tape        # renders docs/assets/demo.gif (the README hero)
vhs demo.tape             # renders demo.gif (plain demo + doctor)
```

The hero GIF already lives at `docs/assets/demo.gif` and is embedded near the top
of the README:

```markdown
![Entropy Loop Core replay demo](./docs/assets/demo.gif)
```

## Alternative: asciinema

```bash
pip install asciinema
asciinema rec demo.cast -c "entropy-loop demo"
```

Upload with `asciinema upload demo.cast` and link the resulting player in the
README.
