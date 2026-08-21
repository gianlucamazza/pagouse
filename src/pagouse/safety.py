"""Page-agent gates. Origin identity lives in policy.py, not here."""

from __future__ import annotations

import os

from pagouse.errors import Readonly


def allow_input_enabled(cli_flag: bool = False) -> bool:
    if cli_flag:
        return True
    if os.environ.get("PAGOUSE_ALLOW_INPUT", "") in {"1", "true", "yes"}:
        return True
    from pagouse.config import load_config

    return load_config().allow_input


def require_input(cli_flag: bool = False) -> None:
    if not allow_input_enabled(cli_flag):
        raise Readonly(
            "input disabled; pass --allow-input, set PAGOUSE_ALLOW_INPUT=1, "
            "or allow_input = true in config"
        )
