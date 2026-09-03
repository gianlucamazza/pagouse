"""Narrow CDP boundary for Chromium's browser-computed AX tree."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from pagouse.errors import IpcFailed

try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None  # type: ignore[assignment]


def _page_socket(debugger_address: str) -> str:
    with urllib.request.urlopen(f"http://{debugger_address}/json/list", timeout=5) as response:
        pages = json.loads(response.read())
    for page in pages:
        if page.get("type") == "page" and page.get("webSocketDebuggerUrl"):
            return str(page["webSocketDebuggerUrl"])
    raise IpcFailed("no debuggable Chromium page")


def command(
    debugger_address: str, method: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    if websocket is None:
        raise IpcFailed("install the websocket-client package")
    try:
        sock = websocket.create_connection(_page_socket(debugger_address), timeout=8)
        sock.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        while True:
            message = json.loads(sock.recv())
            if message.get("id") == 1:
                sock.close()
                if "error" in message:
                    raise IpcFailed(str(message["error"]))
                return message.get("result") or {}
    except (OSError, KeyError, json.JSONDecodeError, websocket.WebSocketException) as exc:
        raise IpcFailed(f"CDP accessibility endpoint unavailable: {exc}") from exc


def accessibility_tree(debugger_address: str) -> list[dict[str, Any]]:
    return command(debugger_address, "Accessibility.getFullAXTree").get("nodes", [])


def normalize(nodes: list[dict[str, Any]]) -> tuple[str, dict[str, int]]:
    """Return compact AX text and backend-node refs for later resolution."""
    lines: list[str] = []
    refs: dict[str, int] = {}
    actionable_roles = {
        "button",
        "link",
        "textbox",
        "checkbox",
        "radio",
        "combobox",
        "menuitem",
        "tab",
    }
    for node in nodes:
        role = str((node.get("role") or {}).get("value") or "generic")
        name = str((node.get("name") or {}).get("value") or "")
        properties = {
            item.get("name"): item.get("value", {}).get("value")
            for item in node.get("properties", [])
        }
        ref = ""
        if role in actionable_roles:
            ref = f"ref_{len(refs) + 1}"
            refs[ref] = int(node.get("backendDOMNodeId") or 0)
        state = " disabled" if properties.get("disabled") is True else ""
        line = f"{role} {name}".strip()
        lines.append(f"- {line}{state}{f' [{ref}]' if ref else ''}")
    return "\n".join(lines), refs
