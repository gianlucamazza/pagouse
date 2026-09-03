"""Mutating page operations. Grant is required; origin policy still applies."""

from __future__ import annotations

import time
from typing import Any

from pagouse.bidi import session
from pagouse.observe import snapshot as take_snapshot
from pagouse.policy import origin_of, require_origin
from pagouse.safety import require_input


def _gate(url: str | None, *, allow_input: bool) -> None:
    require_input(cli_flag=allow_input)
    if url:
        require_origin(url)


def _then(payload: dict[str, Any], then: str, tab_id: str | None, delay_ms: int) -> dict[str, Any]:
    if then == "snapshot":
        if delay_ms > 0:
            time.sleep(delay_ms / 1000)
        payload["snapshot"] = take_snapshot(tab_id)
    return payload


def click(
    ref: str,
    *,
    tab_id: str | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    context = str(tab_id) if tab_id is not None else session().current_context()
    session().pointer(ref, context)
    payload = {"tab_id": context, "ref": ref}
    return _then(payload, then, context, delay_ms)


def fill(
    ref: str,
    value: str,
    *,
    tab_id: str | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    context = str(tab_id) if tab_id is not None else session().current_context()
    session().pointer(ref, context)
    session().key_combo("ctrl+a", context)
    session().keys(value, context)
    payload = {"tab_id": context, "ref": ref, "filled": True}
    return _then(payload, then, context, delay_ms)


def type_text(
    text: str,
    *,
    tab_id: str | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    context = str(tab_id) if tab_id is not None else session().current_context()
    session().keys(text, context)
    payload = {"tab_id": context, "typed": len(text)}
    return _then(payload, then, context, delay_ms)


def key(
    combo: str,
    *,
    tab_id: str | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    context = str(tab_id) if tab_id is not None else session().current_context()
    session().key_combo(combo, context)
    payload = {"tab_id": context, "combo": combo}
    return _then(payload, then, context, delay_ms)


def navigate(
    url: str,
    *,
    tab_id: str | None = None,
    allow_input: bool = False,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    if url not in {"back", "forward"}:
        require_origin(url)
    require_input(cli_flag=allow_input)
    context = str(tab_id) if tab_id is not None else session().current_context()
    session().navigate(context, url)
    payload = {"tab_id": context, "url": url}
    return _then(payload, then, context, delay_ms)


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
    result = session()._require().command("browsingContext.create", {"type": "tab"})
    context = str(result.get("context") or "")
    if url:
        session().navigate(context, url)
    payload = {"tab_id": context, "url": url}
    return _then(payload, then, context, delay_ms)


def tab_focus(tab_id: str, *, allow_input: bool = False) -> dict[str, Any]:
    require_input(cli_flag=allow_input)
    result = session()._require().command("browsingContext.activate", {"context": str(tab_id)})
    return {"tab_id": str(tab_id), "activated": result.get("context", str(tab_id))}


def scroll(
    ref: str,
    *,
    tab_id: str | None = None,
    allow_input: bool = False,
    expected_origin: str | None = None,
    then: str = "none",
    delay_ms: int = 450,
) -> dict[str, Any]:
    _gate(expected_origin, allow_input=allow_input)
    context = str(tab_id) if tab_id is not None else session().current_context()
    session().scroll(ref, context)
    payload = {"tab_id": context, "ref": ref}
    return _then(payload, then, context, delay_ms)


def origin_hint(url: str | None) -> str | None:
    if not url:
        return None
    return origin_of(url) or None
