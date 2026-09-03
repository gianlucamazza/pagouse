# Release

Pagouse is released as a Python package. The v2 runtime owns a temporary
Chromium profile and does not ship an extension or native-messaging host.

## Versioning

Update together:

1. `src/pagouse/__init__.py` — `__version__`;
2. `CHANGELOG.md` — a new `## [X.Y.Z]` section;
3. `uv.lock` through `uv sync` or `uv lock`.

The JSON contract version is independent and must change only when the public
envelope changes. Documentation tests verify version and contract alignment.

## Release gates

```bash
uv sync --group dev
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check src
uv build
PAGOUSE_INSTANCE_SIGNATURE=... uv run pytest -m live
git diff --check
```

The live suite is optional on machines without the approved Chromium instance;
its absence must be recorded rather than treated as a passing browser test.

## Artifacts and publication

`uv build` creates the wheel and source distribution under `dist/`. Inspect
both artifacts, then publish them using the project package registry workflow.
Tagging and pushing require an explicit release decision after all gates pass.

Never publish a release with a red or pending CI check, an unreviewed working
tree, or an unverified live-browser claim.
