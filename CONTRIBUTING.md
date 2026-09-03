# Contributing

Thanks for looking. pagouse is a small Chromium page agent with a focused
WebDriver BiDi runtime and two thin hosts.

## Dev loop

```bash
git clone https://github.com/gianlucamazza/pagouse
cd pagouse
uv sync --group dev

uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check src
uv run pagouse --json doctor
```

`./install.sh` deploys the checkout as a `uv` tool and links the agent skill.
It does not modify Chromium profiles or install an extension.

## Tests

The default suite is hermetic. It formats recorded AX fixtures, mocks the
unix socket, and never touches a live browser or your seat. Keep it that
way — a test that opens the developer's browser is a bug, not a stronger
test.

Anything that needs a real Chromium is gated on `PAGOUSE_INSTANCE_SIGNATURE`.

Two groups deserve a note:

- **`tests/test_layout.py`** enforces the boundary: no seat-adapter
  import, no compositor backend.
- **`tests/test_docs_alignment.py`** compares the docs to the code. **Adding
  a flag, an error code, or an MCP tool will fail CI until you document it.**

## Layout rules

- `src/pagouse/hosts/` — CLI and MCP. Thin. They format envelopes; they do
  not contain logic.
- `src/pagouse/` — the page-agent core and protocol adapters.

Do not add mutate tools to the MCP extra. MCP is observe-only, by design.
Do not add `chrome.debugger` in v0.

## Style

- Code, comments, and docs in English.
- Small modules, no framework. `ruff` with the repo's settings is the
  formatter and the linter; line length is 100. `ty` type-checks `src/`.
- Type hints on public functions. `from __future__ import annotations` at the
  top of every module.
- Errors are `PagouseError` subclasses with a stable `code`. A new code
  needs a row in `docs/json-contract.md`.

## Commits and pull requests

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org):
`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`. Write the body in
prose explaining _why_, not a bullet list of what the diff already shows.

Before opening a PR: `uv run pytest`, `uv run ruff check src tests`,
`uv run ruff format --check src tests`, `uv run ty check src`.
