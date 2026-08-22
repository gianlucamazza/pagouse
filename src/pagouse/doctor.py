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
    extension_version = ""
    all_urls = False
    detail = f"{socket_path()} missing"
    try:
        from pagouse.session import call

        reply = call("ping")
        daemon_ok = True
        extension_ok = bool(reply.get("extension"))
        browser = str(reply.get("browser") or "")
        tabs = int(reply.get("tabs") or 0)
        extension_version = str(reply.get("version") or "")
        all_urls = bool(reply.get("all_urls"))
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
    version_detail = "unknown (stale extension?)"
    if extension_version:
        if extension_version == __version__:
            version_detail = f"{extension_version} matches core"
        else:
            version_detail = (
                f"extension {extension_version} != core {__version__}; "
                "reload the unpacked extension"
            )
    checks.append(
        Check(
            id="extension_version",
            ok=extension_version == "" or extension_version == __version__,
            detail=version_detail,
            blocker=extension_version != "" and extension_version != __version__,
        )
    )
    site_access_detail = (
        "On all sites granted"
        if all_urls
        else "Site access not On all sites; shot will fail "
        "(chrome://extensions → pagouse → Details)"
    )
    checks.append(
        Check(
            id="site_access",
            ok=not extension_ok or all_urls,
            detail=site_access_detail,
            blocker=False,
        )
    )

    blockers = [check.id for check in checks if check.blocker and not check.ok]
    ready = not blockers
    return {
        "ready": ready,
        "observe_ready": ready,
        "shot_ready": ready and all_urls,
        "mutate_ready": ready,
        "version": __version__,
        "session": {
            "daemon": daemon_ok,
            "extension": extension_ok,
            "native_host": host is not None,
            "browser": browser,
            "tabs": tabs,
            "extension_version": extension_version,
            "all_urls": all_urls,
        },
        "checks": [check.__dict__ for check in checks],
        "blockers": blockers,
    }
