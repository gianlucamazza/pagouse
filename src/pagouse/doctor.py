"""Readiness for the owned Chromium/WebDriver BiDi runtime."""

from __future__ import annotations

from pagouse import __version__
from pagouse.bidi import session
from pagouse.models import Check


def run_doctor() -> dict:
    state = session().doctor()
    active = bool(state["active"])
    check = Check("webdriver_bidi", active, "connected" if active else "no managed session", True)
    return {
        "ready": active,
        "observe_ready": active,
        "shot_ready": active,
        "mutate_ready": active,
        "version": __version__,
        "session": state,
        "checks": [check.__dict__],
        "blockers": [] if active else ["webdriver_bidi"],
    }
