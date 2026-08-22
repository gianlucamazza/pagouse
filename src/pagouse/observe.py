"""Read-only page operations. Need a live extension; doctor does not."""

from __future__ import annotations

import time
from typing import Any

from pagouse.contract import DEFAULT_FIT
from pagouse.errors import BadArg, WaitTimeout
from pagouse.session import call
from pagouse.shot import save_data_url


def tabs() -> dict[str, Any]:
    reply = call("tabs")
    return {"tabs": reply.get("tabs") or [], "active": reply.get("active")}


def snapshot(
    tab_id: int | None = None,
    *,
    filter: str = "interactive",
    depth: int = 15,
    max_chars: int = 50000,
) -> dict[str, Any]:
    reply = call(
        "snapshot",
        tab_id=tab_id,
        filter=filter,
        depth=depth,
        max_chars=max_chars,
    )
    data = {
        "tab_id": reply.get("tab_id"),
        "url": reply.get("url"),
        "title": reply.get("title"),
        "tree": reply.get("tree") or "",
        "refs": int(reply.get("refs") or 0),
        "filter": reply.get("filter") or filter,
    }
    if reply.get("frame_errors"):
        data["frame_errors"] = reply["frame_errors"]
    return data


def shot(tab_id: int | None = None, *, fit: int = DEFAULT_FIT) -> dict[str, Any]:
    reply = call("shot", tab_id=tab_id)
    data_url = str(reply.get("data_url") or "")
    width = int(reply.get("width") or 0)
    height = int(reply.get("height") or 0)
    saved = save_data_url(data_url, width=width, height=height, fit=fit)
    result: dict[str, Any] = {
        "tab_id": reply.get("tab_id"),
        "path": saved["path"],
        "width": saved["width"],
        "height": saved["height"],
        "scale": saved["scale"],
    }
    if saved.get("fit_skipped"):
        result["fit_skipped"] = True
    return result


def wait(
    tab_id: int | None = None,
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


def wait_ref(
    tab_id: int | None = None,
    *,
    ref: str,
    timeout_ms: int = 5000,
) -> dict[str, Any]:
    """Poll the extension for a ref using lightweight lookup (no full AX walk)."""
    if timeout_ms <= 0:
        raise BadArg("timeout_ms must be positive")
    reply = call(
        "wait_ref",
        tab_id=tab_id,
        ref=ref,
        timeout_ms=timeout_ms,
    )
    return {
        "tab_id": reply.get("tab_id"),
        "ref": ref,
        "matched": reply.get("matched", False),
        "timeout_ms": timeout_ms,
    }
