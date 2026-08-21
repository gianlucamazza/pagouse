from __future__ import annotations

import pytest

from pagouse.errors import Readonly
from pagouse.safety import allow_input_enabled, require_input


def test_readonly_by_default() -> None:
    assert allow_input_enabled() is False
    with pytest.raises(Readonly):
        require_input()


def test_flag_grants() -> None:
    require_input(cli_flag=True)


def test_env_grants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAGOUSE_ALLOW_INPUT", "1")
    require_input()
