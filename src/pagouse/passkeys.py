"""Safe passkey challenge detection and human-approved provider handoff."""

from __future__ import annotations

import re
from typing import Any

from pagouse.config import load_config
from pagouse.observe import snapshot
from pagouse.policy import origin_of

_PASSKEY_PATTERNS = (
    re.compile(r"\bpasskeys?\b", re.IGNORECASE),
    re.compile(r"\bwebauthn\b", re.IGNORECASE),
    re.compile(r"security\s+key", re.IGNORECASE),
    re.compile(r"use\s+(?:your\s+)?(?:device\s+)?key", re.IGNORECASE),
)


def detect(tree: str) -> bool:
    """Return whether an accessibility tree signals a passkey challenge."""
    return any(pattern.search(tree) for pattern in _PASSKEY_PATTERNS)


def status(tab_id: str | None = None) -> dict[str, Any]:
    """Inspect a page and return a non-sensitive passkey handoff status."""
    page = snapshot(tab_id, filter="all")
    detected = detect(str(page.get("tree") or ""))
    configured = load_config().passkey_provider == "trusted_1password_extension"
    result: dict[str, Any] = {
        "tab_id": page["tab_id"],
        "origin": origin_of(str(page.get("url") or "")),
        "detected": detected,
        "handoff_available": detected and configured,
        "provider": "trusted_1password_extension" if configured else None,
        "status": (
            "requires_user_approval"
            if detected and configured
            else "provider_unavailable"
            if detected
            else "not_detected"
        ),
    }
    if detected and configured:
        result["message"] = (
            "Approve the passkey request in the trusted 1Password/browser flow; "
            "pagouse never reads or exports passkey material."
        )
    elif detected:
        result["message"] = (
            "Configure and pair the 1Password extension in the trusted browser; "
            "pagouse never reads or exports passkey material."
        )
    return result
