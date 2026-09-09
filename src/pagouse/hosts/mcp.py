"""Optional stdio MCP server (extra `pagouse[mcp]`). Observe-only."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

from pagouse.contract import envelope
from pagouse.errors import PagouseError
from pagouse.log import setup


def observe_call(action: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except PagouseError as exc:
        return envelope(ok=False, action=action, error=exc.code, message=exc.message)


def main() -> int:
    setup()
    try:
        from mcp.server.mcpserver import MCPServer
        from mcp.types import ToolAnnotations
    except ImportError:
        sys.stderr.write("pagouse-mcp needs the optional extra: pip/uv install 'pagouse[mcp]'\n")
        return 2

    from pagouse.doctor import run_doctor
    from pagouse.observe import shot as take_shot
    from pagouse.observe import snapshot as take_snapshot
    from pagouse.observe import tabs as list_tabs
    from pagouse.observe import wait as wait_for
    from pagouse.observe import wait_event as wait_event_for
    from pagouse.passkeys import status as passkey_status_for

    server = MCPServer("pagouse")
    readonly = ToolAnnotations(read_only_hint=True)

    @server.tool(annotations=readonly)
    def doctor() -> dict:
        """Managed WebDriver BiDi readiness. Read-only."""
        return observe_call(
            "doctor",
            lambda: envelope(ok=True, action="doctor", data=run_doctor()),
        )

    @server.tool(annotations=readonly)
    def tabs() -> dict:
        """List http(s) tabs. Read-only."""
        return observe_call(
            "tabs",
            lambda: envelope(ok=True, action="tabs", data=list_tabs()),
        )

    @server.tool(annotations=readonly)
    def snapshot(
        tab_id: str | None = None,
        filter: str = "interactive",
        depth: int = 15,
        max_chars: int = 50000,
    ) -> dict:
        """Accessibility tree with ref_N labels. Read-only."""
        return observe_call(
            "snapshot",
            lambda: envelope(
                ok=True,
                action="snapshot",
                data={
                    "snapshot": take_snapshot(
                        tab_id, filter=filter, depth=depth, max_chars=max_chars
                    )
                },
            ),
        )

    @server.tool(annotations=readonly)
    def passkey_status(tab_id: str | None = None) -> dict:
        """Detect a passkey challenge and return a non-sensitive user handoff. Read-only."""
        return observe_call(
            "passkey_status",
            lambda: envelope(
                ok=True,
                action="passkey_status",
                data=passkey_status_for(tab_id),
            ),
        )

    @server.tool(annotations=readonly)
    def wait(
        tab_id: str | None = None,
        url_contains: str | None = None,
        ref: str | None = None,
        timeout_ms: int = 5000,
    ) -> dict:
        """Poll until a URL substring or snapshot ref appears. Read-only."""
        return observe_call(
            "wait",
            lambda: envelope(
                ok=True,
                action="wait",
                data=wait_for(
                    tab_id,
                    url_contains=url_contains,
                    ref=ref,
                    timeout_ms=timeout_ms,
                ),
            ),
        )

    @server.tool(annotations=readonly)
    def wait_event(event_name: str, tab_id: str | None = None, timeout_ms: int = 5000) -> dict:
        """Wait for a WebDriver BiDi event. Read-only."""
        return observe_call(
            "wait_event",
            lambda: envelope(
                ok=True,
                action="wait_event",
                data=wait_event_for(event_name, tab_id, timeout_ms=timeout_ms),
            ),
        )

    @server.tool(annotations=readonly)
    def shot(tab_id: str | None = None, fit: int = 1568) -> dict:
        """Capture the tab viewport. Read-only."""
        return observe_call(
            "shot",
            lambda: envelope(ok=True, action="shot", data={"shot": take_shot(tab_id, fit=fit)}),
        )

    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
