from __future__ import annotations

import io
import json
import socket

from pagouse.ipc import nm_pack, nm_read, recv_line, send_line


def test_nm_roundtrip() -> None:
    payload = {"op": "ping", "id": 1}
    raw = nm_pack(payload)
    parsed = nm_read(io.BytesIO(raw))
    assert parsed == payload


def test_unix_line_roundtrip() -> None:
    a, b = socket.socketpair()
    try:
        send_line(a, {"op": "hello", "ok": True})
        assert recv_line(b) == {"op": "hello", "ok": True}
    finally:
        a.close()
        b.close()


def test_nm_pack_is_little_endian_length() -> None:
    raw = nm_pack({"a": 1})
    body = json.dumps({"a": 1}, separators=(",", ":")).encode()
    assert int.from_bytes(raw[:4], "little") == len(body)
    assert raw[4:] == body
