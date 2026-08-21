"""Readiness: native host, daemon, extension. Hermetic without a browser."""

from __future__ import annotations

from pagouse import __version__
from pagouse.errors import IpcFailed, NoSession
from pagouse.models import Check
from pagouse.paths import HOST_NAME, preferred_host_manifest, socket_path


def run_doctor() -> dict:
    checks: list[Check] = []
    host = preferred_host_manifest()
    checks.append(
        Check(
            id="native_host",
            ok=host is not None,
            detail=str(host) if host else f"{HOST_NAME}.json missing",
            blocker=True,
        )
    )

    daemon_ok = False
    extension_ok = False
    browser = ""
    tabs = 0
    detail = f"{socket_path()} missing"
    try:
        from pagouse.session import call

        reply = call("ping")
        daemon_ok = True
        extension_ok = bool(reply.get("extension"))
        browser = str(reply.get("browser") or "")
        tabs = int(reply.get("tabs") or 0)
        detail = "up"
        if extension_ok and tabs == 0:
            try:
                listed = call("tabs")
                tabs = len(listed.get("tabs") or [])
            except (NoSession, IpcFailed):
                pass
    except (NoSession, IpcFailed) as exc:
        detail = exc.message
    checks.append(Check(id="daemon", ok=daemon_ok, detail=detail, blocker=True))
    checks.append(
        Check(
            id="extension",
            ok=extension_ok,
            detail="connected" if extension_ok else "not connected",
            blocker=True,
        )
    )
    if browser:
        checks.append(Check(id="browser", ok=True, detail=browser, blocker=False))

    blockers = [check.id for check in checks if check.blocker and not check.ok]
    ready = not blockers
    return {
        "ready": ready,
        "observe_ready": ready,
        "shot_ready": ready,
        "mutate_ready": ready,
        "version": __version__,
        "session": {
            "daemon": daemon_ok,
            "extension": extension_ok,
            "native_host": host is not None,
            "browser": browser,
            "tabs": tabs,
        },
        "checks": [check.__dict__ for check in checks],
        "blockers": blockers,
    }
