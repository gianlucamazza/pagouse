from __future__ import annotations

from pathlib import Path

import pytest

from pagouse.config import load_config, parse_config
from pagouse.errors import BadConfig


def test_missing_file_is_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAGOUSE_CONFIG", str(tmp_path / "nope.toml"))
    cfg = load_config()
    assert cfg.allow_input is False
    assert cfg.allow_origins == ()


def test_bare_string_is_one_token() -> None:
    cfg = parse_config({"policy": {"deny_origins": "https://example.com"}})
    assert cfg.deny_origins == ("https://example.com",)


def test_wrong_shape_raises() -> None:
    with pytest.raises(BadConfig):
        parse_config({"policy": {"allow_origins": 1}})
