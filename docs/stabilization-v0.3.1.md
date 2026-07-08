# v0.3.1 — Stabilization

v0.3.1 is a **packaging and typing** pass. It adds no features and changes no
runtime behavior. The goal is to make the package installable, typed, and
PyPI-ready — the sheath and warranty, not a bigger blade.

## What this pass does

- **Typing marker.** Adds `src/entropy_loop_core/py.typed` (PEP 561) so
  downstream users receive the package's type information. Verified present in
  the built wheel.
- **Metadata polish.** `pyproject.toml` now declares `Development Status ::
  4 - Beta` and `Typing :: Typed`, and adds `Issues` and `Changelog` project
  URLs alongside Homepage and Repository.
- **Dev packaging tools.** `build` and `twine` are added to the `dev` optional
  dependencies so contributors can produce and check artifacts locally.
- **Build verification.** `python -m build` produces a wheel and sdist;
  `twine check dist/*` passes. The wheel contains only the package (plus
  `py.typed` and the LICENSE) — no tests or examples.
- **Docs.** Adds a [release checklist](release-checklist.md) covering the
  build/verify/tag flow and a PyPI section gated on explicit approval.

## What this pass does NOT do

- No PyPI publish.
- No version bump (stays at `0.3.0` until a release is cut).
- No tags or GitHub releases.
- No runtime, API, or behavior changes.
- No network calls, external integrations, or new runtime dependencies.

## Verifying locally

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
python -m zipfile -l dist/*.whl   # confirm py.typed present, no tests/examples
```

Install remains **source-based** until PyPI is actually published; the README
carries no PyPI install command and no PyPI badge until then.
