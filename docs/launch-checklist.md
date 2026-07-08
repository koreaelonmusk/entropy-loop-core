# Launch Checklist

A short, reproducible checklist for verifying that a first-time developer can
clone, install, test, and run Entropy Loop Core.

## Fresh clone verification

Run this from an empty directory. It reproduces a new developer's first minutes.

```bash
git clone https://github.com/koreaelonmusk/entropy-loop-core.git
cd entropy-loop-core
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
entropy-loop demo
entropy-loop doctor
python -c "import entropy_loop_core; print(entropy_loop_core.__version__)"
```

Expected: tests pass, lint/format clean, the demo prints a fail → learn → retry
→ success trace, `doctor` reports all checks passed, and the version prints
`0.2.0`.

## Launch checklist

- [ ] CI passes on Python 3.10, 3.11, 3.12
- [ ] Fresh clone works (commands above)
- [ ] `entropy-loop demo` works
- [ ] `entropy-loop doctor` works
- [ ] No private product names in tree or history
- [ ] No personal email in tree or history (GitHub noreply only)
- [ ] No secrets or API keys
- [ ] Release tags exist (`v0.1.0`, `v0.2.0`)
- [ ] README explains the public/private boundary

## Public-safety spot check

```bash
git grep -i -E "api[ _-]?key|secret" -- src/ tests/ examples/   # expect no values
git log --all --pretty="%an <%ae>" | sort -u                    # expect one noreply identity
```

Generic forbidden-category wording (for example the words "API keys" or
"customer data") may appear only inside the public/private boundary docs, where
they describe what must **not** be published. Specific private content must
never appear anywhere.
