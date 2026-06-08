# Contributing to receipts-api-mcp

Thank you for your interest in contributing! This project follows a standard
GitHub-based workflow. Please read this guide before opening a PR.

## Getting Started

```bash
# Clone and set up
git clone https://github.com/chf3198/receipts-api-mcp.git
cd receipts-api-mcp

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (including dev extras)
uv sync --extra dev

# Run tests to verify the setup
uv run pytest -v
```

## Development Workflow

1. **Open an issue first** — describe the bug or feature before writing code.
2. **Fork or branch** — create a branch named `<type>/<issue#>-<short-slug>` (e.g. `fix/8-date-filter-bug`).
3. **Write tests** — new behaviour requires at least one test in `tests/`.
4. **Lint before committing** — `uv run ruff check .` must pass (no errors).
5. **Open a pull request** — link it to the issue with `Closes #N` in the PR body.

## Code Style

- **Formatter / linter**: [ruff](https://docs.astral.sh/ruff/). Config is in `pyproject.toml`.
- Line length: 100 characters.
- Type annotations required for all public functions and parameters.
- No unused imports or variables at merge.

## Running the API Locally

```bash
uv run uvicorn receipts_api.main:app --reload
# Open http://localhost:8000/docs
```

## Project Layout

```
src/receipts_api/      # Application source
  main.py              # App factory + entry point
  data_loader.py       # CSV → in-memory list
  utils.py             # Shared filter/serialise helpers
  routers/
    receipts.py        # /receipts endpoints
    stats.py           # /receipts/stats aggregates
data/                  # CSV data files
tests/                 # pytest smoke tests
docs/                  # GitHub Pages dashboard source
```

## Reporting Bugs

Use the [Bug report](.github/ISSUE_TEMPLATE/bug.yml) template. Include:
- Steps to reproduce
- Expected behaviour
- Actual behaviour
- API response / stack trace if applicable

## License

By contributing you agree your contributions are licensed under the [MIT License](LICENSE).
