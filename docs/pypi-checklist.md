# PyPI publishing checklist

This project publishes to PyPI with **Trusted Publishing** (OIDC) — no long-lived
API token is stored anywhere. The workflow is [`.github/workflows/publish.yml`](../.github/workflows/publish.yml).

Nothing publishes until the PyPI-side trusted publisher below is configured, and
the version is only ever what is committed on `main` (currently `0.3.1`).

## One-time PyPI setup (maintainer)

1. Create a PyPI account and enable 2FA.
2. (Recommended) Rehearse on TestPyPI first — create a TestPyPI account too.
3. Add a **Trusted Publisher** for this package:
   - PyPI → *Your projects* → the project → *Publishing*, or *Account → Publishing*
     for a pending publisher if the project does not exist yet.
   - PyPI project name: `entropy-loop-core`
   - Owner: `koreaelonmusk`
   - Repository: `entropy-loop-core`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`
4. In GitHub → *Settings → Environments*, create an environment named `pypi`
   (optionally add required reviewers so a human approves each publish).

## Publishing a release

Once the trusted publisher is configured:

- Publishing a GitHub Release triggers `publish.yml`, **or**
- run it manually from the Actions tab (*Publish* → *Run workflow*).

The workflow builds the sdist + wheel, runs `twine check`, and uploads to PyPI
via OIDC. To publish the current `v0.3.1`, use *Run workflow* (its release is
already published, so it will not auto-trigger).

## Verify the published package

```bash
python -m venv /tmp/elc-pypi-test
source /tmp/elc-pypi-test/bin/activate
python -m pip install --upgrade pip
python -m pip install entropy-loop-core
entropy-loop replay-demo
entropy-loop doctor
python -c "import entropy_loop_core; print(entropy_loop_core.__version__)"
```

## After the first successful PyPI publish

- Change the README install to:

  ```bash
  pip install entropy-loop-core
  entropy-loop replay-demo
  ```

- Add a PyPI badge (only now that the package is actually live).
- Keep a lower "Development install" section with the source instructions.

## Token fallback (only if not using Trusted Publishing)

If you prefer an API token instead of OIDC: create a scoped PyPI token, store it
as a GitHub Actions secret (never commit it), and switch the publish step to use
it. Trusted Publishing is preferred because there is no secret to leak.
