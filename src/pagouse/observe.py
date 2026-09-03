"""Read-only operations on the managed WebDriver BiDi browser."""

from __future__ import annotations

import time
from typing import Any

from pagouse.bidi import session
from pagouse.cdp import accessibility_tree, normalize
from pagouse.contract import DEFAULT_FIT
from pagouse.errors import BadArg, NoSession, WaitTimeout
from pagouse.shot import save_data_url


def tabs() -> dict[str, Any]:
    contexts = session().contexts()
    rows = [
        {
            "id": item.get("context"),
            "url": item.get("url") or "",
            "title": "",
            "active": index == 0,
            "origin": "",
            "scriptable": True,
        }
        for index, item in enumerate(contexts)
    ]
    return {"tabs": rows, "active": rows[0]["id"] if rows else None}


def snapshot(
    tab_id: str | None = None,
    *,
    filter: str = "interactive",
    depth: int = 15,
    max_chars: int = 50000,
) -> dict[str, Any]:
    current = str(tab_id) if tab_id is not None else session().current_context()
    contexts = session().contexts()
    row = next((item for item in contexts if item.get("context") == current), None)
    if row is None:
        raise NoSession(f"context {current} not found")
    if not session().debugger_address:
        raise NoSession("Chromium did not expose a local CDP endpoint for AX")
    tree, refs = normalize(accessibility_tree(session().debugger_address))
    session().set_refs(refs)
    data = {
        "tab_id": current,
        "url": row.get("url") or "",
        "title": "",
        "tree": tree[:max_chars],
        "refs": len(refs),
        "filter": filter,
    }
    return data


def shot(tab_id: str | None = None, *, fit: int = DEFAULT_FIT) -> dict[str, Any]:
    current = str(tab_id) if tab_id is not None else session().current_context()
    reply = session()._require().command("browsingContext.captureScreenshot", {"context": current})
    data_url = "data:image/png;base64," + str(reply.get("data") or "")
    width = height = 0
    saved = save_data_url(data_url, width=width, height=height, fit=fit)
    result: dict[str, Any] = {
        "tab_id": current,
        "path": saved["path"],
        "width": saved["width"],
        "height": saved["height"],
        "scale": saved["scale"],
    }
    if saved.get("fit_skipped"):
        result["fit_skipped"] = True
    return result


def wait(
    tab_id: str | None = None,
    *,
    url_contains: str | None = None,
    ref: str | None = None,
    timeout_ms: int = 5000,
) -> dict[str, Any]:
    """Poll until URL substring or ref appears, or raise WaitTimeout."""
    if timeout_ms <= 0:
        raise BadArg("timeout_ms must be positive")
    needle = (url_contains or "").strip()
    want_ref = (ref or "").strip()
    if not needle and not want_ref:
        raise BadArg("wait needs --url-contains or --ref")
    deadline = time.monotonic() + timeout_ms / 1000
    last_url = ""
    last_tab = tab_id
    while time.monotonic() < deadline:
        if needle:
            listed = tabs()
            rows = listed.get("tabs") or []
            for row in rows:
                if tab_id is not None and row.get("id") != tab_id:
                    continue
                url = str(row.get("url") or "")
                if needle in url:
                    return {
                        "tab_id": row.get("id"),
                        "url": url,
                        "matched": "url",
                        "timeout_ms": timeout_ms,
                    }
                if tab_id is not None:
                    last_url = url
        if want_ref:
            snap = snapshot(tab_id)
            last_tab = snap.get("tab_id")
            last_url = str(snap.get("url") or last_url)
            token = f"[{want_ref}]"
            if token in (snap.get("tree") or ""):
                return {
                    "tab_id": last_tab,
                    "url": last_url,
                    "matched": "ref",
                    "timeout_ms": timeout_ms,
                }
        time.sleep(0.2)
    raise WaitTimeout(
        f"wait timed out after {timeout_ms}ms" + (f" (url={last_url})" if last_url else "")
    )


def wait_event(
    event_name: str,
    tab_id: str | None = None,
    *,
    timeout_ms: int = 5000,
) -> dict[str, Any]:
    """Wait for one subscribed WebDriver BiDi event."""
    if not event_name.strip():
        raise BadArg("event_name must not be empty")
    context = str(tab_id) if tab_id is not None else None
    event = session().wait_event(event_name, timeout_ms, context)
    return {"event": event_name, "tab_id": context, "payload": event, "timeout_ms": timeout_ms}
