from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pagouse.credentials import load_credentials, resolve
from pagouse.errors import (
    BadConfig,
    CredentialFieldInvalid,
    CredentialNotFound,
    SecretResolutionFailed,
)


def _write(path: Path, text: str, mode: int = 0o600) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


def test_loads_only_secret_references(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    _write(
        path,
        '[credentials.demo]\norigin = "https://example.com"\n'
        'username = "op://Pagouse/Demo/username"\n'
        'password = "op://Pagouse/Demo/password"\n',
    )
    credentials = load_credentials(path)
    assert credentials["demo"].password == "op://Pagouse/Demo/password"


def test_rejects_loose_permissions(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    _write(
        path,
        '[credentials.demo]\norigin = "https://example.com"\npassword = "op://v/i/password"\n',
        0o644,
    )
    with pytest.raises(BadConfig):
        load_credentials(path)


def test_rejects_unknown_field_or_handle(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    _write(
        path, '[credentials.demo]\norigin = "https://example.com"\npassword = "op://v/i/password"\n'
    )
    with pytest.raises(CredentialFieldInvalid):
        resolve("demo", "otp", path)
    with pytest.raises(CredentialNotFound):
        resolve("missing", "password", path)


def test_resolve_uses_op_without_exposing_value_in_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "credentials.toml"
    _write(
        path, '[credentials.demo]\norigin = "https://example.com"\npassword = "op://v/i/password"\n'
    )
    seen: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        seen.append(args)
        assert kwargs["capture_output"] is True
        return subprocess.CompletedProcess(args, 0, stdout=b"not-in-argv", stderr=b"")

    monkeypatch.setattr("pagouse.credentials.shutil.which", lambda _: "/usr/bin/op")
    monkeypatch.setattr("pagouse.credentials.subprocess.run", fake_run)
    assert resolve("demo", "password", path) == "not-in-argv"
    assert "not-in-argv" not in " ".join(seen[0])
    assert seen[0] == ["/usr/bin/op", "read", "--no-newline", "op://v/i/password"]


def test_invalid_provider_output_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "credentials.toml"
    _write(
        path, '[credentials.demo]\norigin = "https://example.com"\npassword = "op://v/i/password"\n'
    )
    monkeypatch.setattr("pagouse.credentials.shutil.which", lambda _: "/usr/bin/op")
    monkeypatch.setattr(
        "pagouse.credentials.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=b"\xff", stderr=b""),
    )
    with pytest.raises(SecretResolutionFailed, match="invalid text"):
        resolve("demo", "password", path)


def test_origin_is_required_and_canonicalized(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    _write(
        path,
        '[credentials.demo]\norigin = "https://Example.com:443/"\npassword = "op://v/i/password"\n',
    )
    assert load_credentials(path)["demo"].origin == "https://example.com"
