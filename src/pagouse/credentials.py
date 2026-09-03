"""Restricted 1Password secret-reference broker for page input."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from pagouse.errors import (
    BadConfig,
    CredentialFieldInvalid,
    CredentialNotFound,
    SecretProviderUnavailable,
    SecretResolutionFailed,
)

_REFERENCE = re.compile(r"^op://[^/\r\n]+/[^/\r\n]+(?:/[^/\r\n]+)?/[^/\r\n]+$")
_FIELDS = frozenset({"username", "password"})


@dataclass(frozen=True)
class Credential:
    origin: str
    username: str | None = None
    password: str | None = None


def credentials_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "pagouse" / "credentials.toml"


def _check_permissions(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise BadConfig(f"{path}: cannot inspect permissions") from exc
    if mode & 0o077:
        raise BadConfig(f"{path}: permissions must be 0600 or stricter")


def _reference(value: object, *, key: str) -> str:
    if not isinstance(value, str) or not _REFERENCE.fullmatch(value):
        raise BadConfig(f"credentials.{key} must be an op:// secret reference")
    return value


def _origin(value: object, *, key: str) -> str:
    if not isinstance(value, str):
        raise BadConfig(f"credentials.{key} must be an http(s) origin")
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise BadConfig(f"credentials.{key} must be an http(s) origin")
    try:
        port = parsed.port
    except ValueError as exc:
        raise BadConfig(f"credentials.{key} must be an http(s) origin") from exc
    default_port = (parsed.scheme == "http" and port == 80) or (
        parsed.scheme == "https" and port == 443
    )
    suffix = "" if port is None or default_port else f":{port}"
    return f"{parsed.scheme}://{parsed.hostname}{suffix}".lower()


def load_credentials(path: Path | None = None) -> dict[str, Credential]:
    target = path or credentials_path()
    if not target.is_file():
        return {}
    _check_permissions(target)
    import tomllib

    try:
        data = tomllib.loads(target.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError) as exc:
        raise BadConfig(f"{target}: {exc}") from exc
    table = data.get("credentials")
    if not isinstance(table, dict):
        raise BadConfig("credentials must be a table")
    result: dict[str, Credential] = {}
    for handle, value in table.items():
        if not isinstance(handle, str) or not handle or not isinstance(value, dict):
            raise BadConfig("credential handles must map to tables")
        origin = _origin(value.get("origin"), key=f"{handle}.origin")
        username = value.get("username")
        password = value.get("password")
        result[handle] = Credential(
            origin=origin,
            username=(
                _reference(username, key=f"{handle}.username") if username is not None else None
            ),
            password=(
                _reference(password, key=f"{handle}.password") if password is not None else None
            ),
        )
    return result


def origin_for(handle: str, path: Path | None = None) -> str:
    credential = load_credentials(path).get(handle)
    if credential is None:
        raise CredentialNotFound(handle)
    return credential.origin


def resolve(handle: str, field: str, path: Path | None = None) -> str:
    if field not in _FIELDS:
        raise CredentialFieldInvalid(field)
    credential = load_credentials(path).get(handle)
    if credential is None:
        raise CredentialNotFound(handle)
    reference = getattr(credential, field)
    if reference is None:
        raise CredentialFieldInvalid(f"{handle}.{field} is not configured")
    executable = shutil.which("op")
    if not executable:
        raise SecretProviderUnavailable("1Password CLI (`op`) is not installed")
    try:
        result = subprocess.run(
            [executable, "read", "--no-newline", reference],
            check=True,
            capture_output=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SecretResolutionFailed("1Password CLI could not resolve the reference") from exc
    except subprocess.CalledProcessError as exc:
        raise SecretResolutionFailed("1Password CLI rejected the secret reference") from exc
    try:
        value = result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SecretResolutionFailed("1Password returned an invalid text value") from exc
    if not value:
        raise SecretResolutionFailed("1Password returned an empty value")
    return value
