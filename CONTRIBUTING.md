# Contributing

Thanks for your interest in Entropy Loop Core. This project values a small,
readable core, so contributions that keep it simple are especially welcome.

## Getting started

```bash
git clone https://github.com/koreaelonmusk/entropy-loop-core.git
cd entropy-loop-core
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Development workflow

1. Create a branch for your change.
2. Make your change with tests and docstrings.
3. Run the checks below.
4. Open a pull request with a clear description.

## Checks

```bash
ruff check .        # lint
ruff format .       # format
pytest              # tests
```

Please make sure lint and tests pass before opening a PR.

## Guidelines

- Keep the public API small and well documented.
- Keep the core deterministic: no LLM calls, no network I/O, no randomness in
  lesson or regression generation.
- Prefer plain callables over class hierarchies.
- Add or update tests for any behavior change.
- Do not add proprietary, vendor-specific, or business logic.
- Match the style of the surrounding code.

## Reporting issues

Open a GitHub issue with a minimal reproduction and what you expected to happen.

By contributing you agree that your contributions are licensed under the
project's Apache-2.0 license.
