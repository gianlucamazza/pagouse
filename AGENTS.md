# AGENTS.md

Notes for coding agents working **on** this repository. To _use_ pagouse to
drive a page, read `skills/pagouse/SKILL.md` instead.

## Read first

- [CONTRIBUTING.md](CONTRIBUTING.md) — dev loop, test suite, layout rules,
  commit convention.
- [docs/json-contract.md](docs/json-contract.md) — the `--json` envelope is
  the contract (`schema: 1`). Do not invent fields.
- [docs/architecture.md](docs/architecture.md) — page agent, not a seat
  adapter.

## Hard rules

- Do not import a seat-adapter library. This core is page-only.
- MCP stays observe-only. Do not add a mutate tool to it.
- No `chrome.debugger` in v0.
- Errors are `PagouseError` subclasses with a stable `code`. A new code
  needs a row in `docs/json-contract.md`.
- The default test suite is hermetic: recorded AX fixtures, mocked sockets,
  no live browser. Gate anything else on `PAGOUSE_INSTANCE_SIGNATURE`.
- Comments and documentation in English.

## Docs are tested

`tests/test_docs_alignment.py` compares the documentation to the code. A
change to the surface that skips the docs will fail, by design.
