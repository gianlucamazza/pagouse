"""Structured errors for the CLI / MCP JSON envelope."""

from __future__ import annotations

__all__ = [
    "BadArg",
    "BadConfig",
    "Denied",
    "IpcFailed",
    "NoSession",
    "NoTab",
    "OriginChanged",
    "PagouseError",
    "Readonly",
    "RestrictedPage",
    "StaleRef",
    "WaitTimeout",
]


class PagouseError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class NoSession(PagouseError):
    def __init__(self, message: str = "extension or daemon not connected") -> None:
        super().__init__("no_session", message)


class NoTab(PagouseError):
    def __init__(self, tab_id: int | None = None) -> None:
        detail = "no usable tab" if tab_id is None else f"tab {tab_id} not found"
        super().__init__("no_tab", detail)
        self.tab_id = tab_id


class StaleRef(PagouseError):
    def __init__(self, ref: str) -> None:
        super().__init__("stale_ref", f"{ref} is no longer in the document")
        self.ref = ref


class IpcFailed(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("ipc_failed", detail)


class RestrictedPage(PagouseError):
    """Chromium forbids scripting this page (Web Store gallery, chrome pages)."""

    def __init__(self, detail: str) -> None:
        super().__init__("restricted_page", detail)


class Readonly(PagouseError):
    def __init__(self, message: str = "input disabled (readonly)") -> None:
        super().__init__("readonly", message)


class Denied(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("denied", detail)


class OriginChanged(PagouseError):
    def __init__(self, detail: str = "tab origin changed during the action") -> None:
        super().__init__("origin_changed", detail)


class BadConfig(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("bad_config", detail)


class BadArg(PagouseError):
    def __init__(self, detail: str) -> None:
        super().__init__("bad_arg", detail)


class WaitTimeout(PagouseError):
    def __init__(self, detail: str = "wait timed out") -> None:
        super().__init__("wait_timeout", detail)
