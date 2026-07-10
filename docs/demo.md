# Recording the demo

A recorded GIF lives at [`docs/assets/demo.gif`](assets/demo.gif) and is shown in
the README. This page explains how to (re)generate it from the real CLI.

There are three tape scripts:

- [`docs/assets/demo-v1.tape`](assets/demo-v1.tape) — the **README demo GIF** for
  the v1.0.0 launch: version → `doctor` → `replay-demo` → CI reports
  (JSON / Markdown / JUnit XML / HTML) → Korean HTML console → stability contract.
  This is what renders `docs/assets/demo.gif`.
- [`demo.hero.tape`](../demo.hero.tape) — an older, cinematic take on
  `entropy-loop replay-demo` (narrative frame, then the real command).
- [`demo.tape`](../demo.tape) — a plain, lower-level recording of
  `entropy-loop demo` + `doctor`.

## What the demo shows

The v1.0.0 demo is a short tour of the real CLI — no fake output, no network:

1. the installed package reports version `1.0.0`;
2. `entropy-loop doctor` passes;
3. `entropy-loop replay-demo` captures a failure and replays it as a regression;
4. `entropy-loop compare-reports` writes JSON, Markdown, JUnit XML, and an HTML
   failure console in one run;
5. the same command writes a Korean HTML console with `--html-locale ko`;
6. `entropy-loop contract` prints the deterministic boundaries and
   `package_version` `1.0.0`.

`entropy-loop demo` (shown by the older tapes) runs a fake agent that fails once (a
required term is missing), then compiles the failure into a lesson, retries with
that lesson in context, and succeeds — printing the category, fingerprint, an
evaluation summary, and a generated regression case.

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
brew install vhs             # or: go install github.com/charmbracelet/vhs@latest
pip install -e ".[dev]"      # so `entropy-loop` is on PATH
vhs docs/assets/demo-v1.tape # renders docs/assets/demo.gif (the README demo)
vhs demo.hero.tape           # older cinematic replay-demo take
vhs demo.tape                # plain demo + doctor
```

The demo GIF lives at `docs/assets/demo.gif` and is embedded near the top of the
README:

```markdown
![Entropy Loop Core v1.0.0 demo: version, doctor, replay, CI reports (JSON/Markdown/JUnit/HTML), Korean console, and the stability contract](./docs/assets/demo.gif)
```

## Alternative: asciinema

```bash
pip install asciinema
asciinema rec demo.cast -c "entropy-loop demo"
```

Upload with `asciinema upload demo.cast` and link the resulting player in the
README.
