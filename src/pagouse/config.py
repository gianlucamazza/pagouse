"""Optional user config. Origin policy tokens come from the user, not a catalog."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pagouse.errors import BadConfig


@dataclass(frozen=True)
class Config:
    allow_input: bool = False
    allow_origins: tuple[str, ...] = ()
    deny_origins: tuple[str, ...] = ()
    passkey_provider: str = "none"


def config_path() -> Path:
    override = os.environ.get("PAGOUSE_CONFIG")
    if override:
        return Path(override)
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "pagouse" / "config.toml"


def load_config(path: Path | None = None) -> Config:
    target = path or config_path()
    if not target.is_file():
        return Config()
    import tomllib

    try:
        data = tomllib.loads(target.read_text())
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError) as exc:
        raise BadConfig(f"{target}: {exc}") from exc
    return parse_config(data)


def _str_tuple(value: Any, key: str) -> tuple[str, ...]:
    """A bare string is one token, never a sequence of characters."""
    if isinstance(value, str):
        return (value,) if value else ()
    if not isinstance(value, (list, tuple)):
        raise BadConfig(f"{key} must be a list of strings, got {type(value).__name__}")
    return tuple(str(x) for x in value)


def parse_config(data: dict[str, Any]) -> Config:
    if not isinstance(data, dict):
        raise BadConfig("config root must be a table")
    policy = data.get("policy") or {}
    if policy and not isinstance(policy, dict):
        raise BadConfig("policy must be a table")
    allow = data.get("allow_input", policy.get("allow_input", False))
    allow_origins = policy.get("allow_origins") or data.get("allow_origins") or []
    deny_origins = policy.get("deny_origins") or data.get("deny_origins") or []
    passkey = data.get("passkey") or {}
    if not isinstance(passkey, dict):
        raise BadConfig("passkey must be a table")
    passkey_provider = passkey.get("provider", "none")
    if passkey_provider not in {"none", "trusted_1password_extension"}:
        raise BadConfig("passkey.provider must be 'none' or 'trusted_1password_extension'")
    return Config(
        allow_input=bool(allow),
        allow_origins=_str_tuple(allow_origins, "allow_origins"),
        deny_origins=_str_tuple(deny_origins, "deny_origins"),
        passkey_provider=passkey_provider,
    )
