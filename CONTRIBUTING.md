# Contributing

Contributions are welcome. This project is designed as a reference implementation, so the bar for changes is: does this make the patterns clearer or more useful for engineering teams adopting Codex?

## Setup

```bash
git clone https://github.com/agaleaniket10/codex-sdlc-copilot.git
cd codex-sdlc-copilot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install ruff pytest
```

## Running tests

```bash
pytest tests/ -v
```

All tests run offline — no API key required.

## Linting

```bash
ruff check .
```

All PRs must pass `ruff check` and `pytest tests/` with zero failures.

## Adding a new mode

1. Create `cli/<mode_name>.py` with a `run()` function and a `SYSTEM_PROMPT`
2. Register the CLI command in `cli/main.py`
3. Add tests in `tests/test_cli.py` (mock the `CodexAgent`)
4. Add a workshop lab in `workshop/`
5. Document the pattern in `GUIDE.md`

## Submitting a PR

- Keep PRs focused — one mode or one fix per PR
- Include a brief description of what changed and why
- Reference any related issues
