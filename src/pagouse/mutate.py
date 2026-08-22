"""Mutating page operations. Grant is required; origin policy still applies."""

from __future__ import annotations

import time
from typing import Any

from pagouse.observe import snapshot as take_snapshot
from pagouse.policy import origin_of, require_origin
from pagouse.safety import require_input
from pagouse.session import call


def _gate(url: str | None, *, allow_input: bool) -> None:
    require_input(cli_flag=allow_input)
    if url:
        require_origin(url)


def _then(payload: dict[str, Any], then: str, tab_id: int | None, delay_ms: int) -> dict[str, Any]:
    if then == "snapshot":
        if delay_ms > 0:
            time.sleep(delay_ms / 1000)
        payload["snapshot"] = take_snapshot(tab_id)
    return payload


def click(
    ref: str,
    *,
    tab_id: int | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    reply = call(
        "click",
        ref=ref,
        tab_id=tab_id,
        allow_input=allow_input,
        expected_origin=expected_origin,
    )
    payload = {"tab_id": reply.get("tab_id"), "ref": ref}
    return _then(payload, then, reply.get("tab_id") if tab_id is None else tab_id, delay_ms)


def fill(
    ref: str,
    value: str,
    *,
    tab_id: int | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    reply = call(
        "fill",
        ref=ref,
        value=value,
        tab_id=tab_id,
        allow_input=allow_input,
        expected_origin=expected_origin,
    )
    payload = {"tab_id": reply.get("tab_id"), "ref": ref, "filled": True}
    return _then(payload, then, reply.get("tab_id") if tab_id is None else tab_id, delay_ms)


def type_text(
    text: str,
    *,
    tab_id: int | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    reply = call(
        "type",
        text=text,
        tab_id=tab_id,
        allow_input=allow_input,
        expected_origin=expected_origin,
    )
    payload = {"tab_id": reply.get("tab_id"), "typed": len(text)}
    return _then(payload, then, reply.get("tab_id") if tab_id is None else tab_id, delay_ms)


def key(
    combo: str,
    *,
    tab_id: int | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    reply = call(
        "key",
        combo=combo,
        tab_id=tab_id,
        allow_input=allow_input,
        expected_origin=expected_origin,
    )
    payload = {"tab_id": reply.get("tab_id"), "combo": combo}
    return _then(payload, then, reply.get("tab_id") if tab_id is None else tab_id, delay_ms)


def navigate(
    url: str,
    *,
    tab_id: int | None = None,
    allow_input: bool = False,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    if url not in {"back", "forward"}:
        require_origin(url)
    require_input(cli_flag=allow_input)
    reply = call("navigate", url=url, tab_id=tab_id, allow_input=allow_input)
    payload = {"tab_id": reply.get("tab_id"), "url": reply.get("url") or url}
    return _then(payload, then, reply.get("tab_id") if tab_id is None else tab_id, delay_ms)


def tab_open(
    url: str | None = None,
    *,
    allow_input: bool = False,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    require_input(cli_flag=allow_input)
    if url:
        require_origin(url)
    reply = call("tab_open", url=url, allow_input=allow_input)
    payload = {"tab_id": reply.get("tab_id"), "url": reply.get("url") or url}
    return _then(payload, then, reply.get("tab_id"), delay_ms)


def tab_focus(tab_id: int, *, allow_input: bool = False) -> dict[str, Any]:
    require_input(cli_flag=allow_input)
    reply = call("tab_focus", tab_id=tab_id, allow_input=allow_input)
    return {"tab_id": reply.get("tab_id") or tab_id}


def scroll(
    ref: str,
    *,
    tab_id: int | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    reply = call(
        "scroll",
        ref=ref,
        tab_id=tab_id,
        allow_input=allow_input,
        expected_origin=expected_origin,
    )
    payload = {"tab_id": reply.get("tab_id"), "ref": ref}
    return _then(payload, then, reply.get("tab_id") if tab_id is None else tab_id, delay_ms)


def origin_hint(url: str | None) -> str | None:
    if not url:
        return None
    return origin_of(url) or None
