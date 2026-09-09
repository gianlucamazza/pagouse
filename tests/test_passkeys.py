from __future__ import annotations

from typing import Any

from pagouse.passkeys import detect, status


def test_detects_passkey_language_without_returning_page_content() -> None:
    assert detect("Sign in with a passkey")
    assert detect("Use your security key")
    assert detect("WebAuthn authentication required")
    assert not detect("Enter your password")


def test_status_is_a_non_sensitive_handoff(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "pagouse.passkeys.snapshot",
        lambda tab_id=None, **kwargs: {
            "tab_id": tab_id or "ctx",
            "url": "https://github.com/login",
            "tree": "Continue with a passkey",
        },
    )
    monkeypatch.setenv("PAGOUSE_CONFIG", "/nonexistent/pagouse-config.toml")

    result = status("ctx")

    assert result == {
        "tab_id": "ctx",
        "origin": "https://github.com",
        "detected": True,
        "handoff_available": False,
        "provider": None,
        "status": "provider_unavailable",
        "message": (
            "Configure and pair the 1Password extension in the trusted browser; "
            "pagouse never reads or exports passkey material."
        ),
    }
    assert all(secret not in str(result) for secret in ("assertion", "private_key"))


def test_status_is_not_detected_without_challenge(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "pagouse.passkeys.snapshot",
        lambda tab_id=None, **kwargs: {
            "tab_id": "ctx",
            "url": "https://example.com",
            "tree": "Username\nPassword",
        },
    )

    assert status() == {
        "tab_id": "ctx",
        "origin": "https://example.com",
        "detected": False,
        "handoff_available": False,
        "provider": None,
        "status": "not_detected",
    }


def test_configured_provider_requires_human_approval(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "pagouse.passkeys.snapshot",
        lambda tab_id=None, **kwargs: {
            "tab_id": "ctx",
            "url": "https://github.com/login",
            "tree": "Sign in with a passkey",
        },
    )
    monkeypatch.setattr(
        "pagouse.passkeys.load_config",
        lambda: type("Config", (), {"passkey_provider": "trusted_1password_extension"})(),
    )

    result = status()

    assert result["handoff_available"] is True
    assert result["provider"] == "trusted_1password_extension"
    assert result["status"] == "requires_user_approval"
