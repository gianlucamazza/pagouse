"""Talk to the local daemon. Observation never starts it; the extension does."""

from __future__ import annotations

import socket
from typing import Any

from pagouse.errors import (
    BadArg,
    Denied,
    IpcFailed,
    NoSession,
    NoTab,
    OriginChanged,
    PagouseError,
    StaleRef,
    WaitTimeout,
)
from pagouse.ipc import recv_line, send_line
from pagouse.paths import socket_path

_TIMEOUT = 8.0


def connect() -> socket.socket:
    path = socket_path()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(_TIMEOUT)
    try:
        sock.connect(str(path))
    except OSError as exc:
        sock.close()
        raise NoSession(f"daemon not running ({path})") from exc
    return sock


def call(op: str, **params: Any) -> dict[str, Any]:
    """One request/reply. Raises PagouseError on a structured failure."""
    req = {"op": op, **{k: v for k, v in params.items() if v is not None}}
    sock = connect()
    try:
        send_line(sock, req)
        reply = recv_line(sock)
    except OSError as exc:
        raise IpcFailed(str(exc)) from exc
    finally:
        sock.close()
    if reply.get("ok") is False:
        code = str(reply.get("error") or "ipc_failed")
        message = str(reply.get("message") or code)
        if code == "no_session":
            raise NoSession(message)
        if code == "no_tab":
            raw = params.get("tab_id")
            raise NoTab(int(raw) if raw is not None else None)
        if code == "stale_ref":
            raise StaleRef(str(params.get("ref") or ""))
        if code == "denied":
            raise Denied(message)
        if code == "origin_changed":
            raise OriginChanged(message)
        if code == "bad_arg":
            raise BadArg(message)
        if code == "ipc_failed":
            raise IpcFailed(message)
        if code == "wait_timeout":
            raise WaitTimeout(message)
        raise PagouseError(code, message)
    return reply
