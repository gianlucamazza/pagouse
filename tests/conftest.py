from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _isolate_xdg(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("PAGOUSE_CONFIG", raising=False)
    monkeypatch.delenv("PAGOUSE_ALLOW_INPUT", raising=False)
    (tmp_path / "run").mkdir()
    (tmp_path / "config").mkdir()
    os.environ.setdefault("XDG_RUNTIME_DIR", str(tmp_path / "run"))
