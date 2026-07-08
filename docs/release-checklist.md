# Release checklist

Steps for cutting a release. Publishing to PyPI is **gated on explicit approval**
and is not part of the normal flow yet.

## Before tagging

- [ ] `pytest` passes
- [ ] `ruff check .` and `ruff format --check .` are clean
- [ ] `entropy-loop demo`, `entropy-loop doctor`, `entropy-loop replay-demo` run
- [ ] `python -c "import entropy_loop_core; print(entropy_loop_core.__version__)"`
- [ ] version bumped in `pyproject.toml` **and** `src/entropy_loop_core/__init__.py`
- [ ] `CHANGELOG.md` has an entry for the new version
- [ ] CI is green on `main` (Python 3.10 / 3.11 / 3.12)
- [ ] public-safety grep is clean (no private names, emails, or secrets)

## Build and verify artifacts

```bash
rm -rf dist build
python -m build
twine check dist/*
```

- [ ] `twine check` passes for the wheel and the sdist
- [ ] wheel includes `entropy_loop_core/py.typed`
- [ ] wheel does **not** include `tests/` or `examples/`
- [ ] wheel `dist-info` includes the LICENSE

Inspect:

```bash
python -m zipfile -l dist/*.whl
tar tzf dist/*.tar.gz
```

## Tag and GitHub Release

```bash
git tag -a vX.Y.Z -m "Entropy Loop Core vX.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "Entropy Loop Core vX.Y.Z" \
  --notes-file <notes>.md --latest
```

- [ ] annotated tag pushed and confirmed on remote
- [ ] Release notes reviewed (no broken code fences)
- [ ] Release marked latest

## PyPI (only when explicitly approved)

Not yet enabled. When approved:

```bash
twine upload --repository testpypi dist/*   # rehearse on TestPyPI first
twine upload dist/*                          # PyPI
```

- [ ] rehearsed on TestPyPI
- [ ] README renders correctly on the package page
- [ ] only then add a PyPI install command / badge to the README

Rules: no force-push, no history rewrite, no tag edits, fix-forward only.
