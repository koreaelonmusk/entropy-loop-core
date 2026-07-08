# Recording the demo

There is **no GIF committed to this repository**. This page explains how to
record one from the real CLI so the README can show the loop in motion.

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
vhs demo.tape             # produces demo.gif
```

The tape script lives at [`demo.tape`](../demo.tape). Once you have `demo.gif`,
add it near the top of the README, for example:

```markdown
![entropy-loop demo](demo.gif)
```

## Alternative: asciinema

```bash
pip install asciinema
asciinema rec demo.cast -c "entropy-loop demo"
```

Upload with `asciinema upload demo.cast` and link the resulting player in the
README.
