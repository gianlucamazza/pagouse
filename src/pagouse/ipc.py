"""Framing: native-messaging length prefix, and newline JSON on the unix socket."""

from __future__ import annotations

import json
import struct
from socket import socket
from typing import Any, BinaryIO

MAX_NM_FRAME = 64 * 1024 * 1024
MAX_LINE = 64 * 1024 * 1024


def nm_pack(obj: dict[str, Any]) -> bytes:
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return struct.pack("<I", len(raw)) + raw


def nm_read(inp: BinaryIO, timeout_unused: float | None = None) -> dict[str, Any] | None:
    header = inp.read(4)
    if not header:
        return None
    if len(header) < 4:
        raise OSError("native-messaging header truncated")
    (length,) = struct.unpack("<I", header)
    if length > MAX_NM_FRAME:
        raise OSError(f"native-messaging frame too large ({length} bytes)")
    raw = inp.read(length)
    if len(raw) < length:
        raise OSError("native-messaging payload truncated")
    payload = json.loads(raw.decode())
    if not isinstance(payload, dict):
        raise OSError("native-messaging payload is not an object")
    return payload


def send_line(sock: socket, obj: dict[str, Any]) -> None:
    raw = json.dumps(obj, separators=(",", ":")).encode() + b"\n"
    if len(raw) > MAX_LINE:
        raise OSError(f"unix message too large ({len(raw)} bytes)")
    sock.sendall(raw)


def recv_line(sock: socket) -> dict[str, Any]:
    buf = bytearray()
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            raise OSError("daemon socket closed")
        buf.extend(chunk)
        if len(buf) > MAX_LINE:
            raise OSError("unix message too large")
        if b"\n" in buf:
            line, rest = buf.split(b"\n", 1)
            if rest:
                # Caller must be line-oriented one-message-at-a-time; leftover
                # is a protocol error (one request, one reply).
                pass
            payload = json.loads(bytes(line).decode())
            if not isinstance(payload, dict):
                raise OSError("daemon sent a non-object message")
            return payload
