"""Readiness for the owned Chromium/WebDriver BiDi runtime."""

from __future__ import annotations

from pagouse import __version__
from pagouse.bidi import session
from pagouse.config import load_config
from pagouse.models import Check


def run_doctor() -> dict:
    state = session().doctor()
    active = bool(state["active"])
    check = Check("webdriver_bidi", active, "connected" if active else "no managed session", True)
    trusted_configured = load_config().passkey_provider == "trusted_1password_extension"
    passkey_check = Check(
        "trusted_1password_extension",
        trusted_configured,
        "configured; verify extension pairing in the trusted browser"
        if trusted_configured
        else "not configured; passkey approval remains external",
        False,
    )
    return {
        "ready": active,
        "observe_ready": active,
        "shot_ready": active,
        "mutate_ready": active,
        "version": __version__,
        "session": state,
        "checks": [check.__dict__, passkey_check.__dict__],
        "trusted_extension_configured": trusted_configured,
        "trusted_browser_required": True,
        "blockers": [] if active else ["webdriver_bidi"],
    }
