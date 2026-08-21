"""Native-messaging relay. Chromium spawns this; it speaks to pagoused."""

from __future__ import annotations

import os
import select
import shutil
import socket
import subprocess
import sys
import time
from typing import Any

from pagouse.ipc import nm_pack, nm_read, recv_line, send_line
from pagouse.paths import socket_path

_ENSURE_TRIES = 50


def _ping(path: Any) -> bool:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    try:
        sock.connect(str(path))
        send_line(sock, {"op": "ping"})
        return True
    except OSError:
        return False
    finally:
        sock.close()


def ensure_daemon() -> None:
    path = socket_path()
    if _ping(path):
        return
    binary = shutil.which("pagoused")
    cmd = [binary] if binary else [sys.executable, "-m", "pagouse.daemon"]
    subprocess.Popen(
        cmd,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ,
    )
    for _ in range(_ENSURE_TRIES):
        time.sleep(0.05)
        if _ping(path):
            return
    sys.stderr.write("pagouse-nm: pagoused failed to start\n")
    raise SystemExit(1)


def _connect() -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(str(socket_path()))
    send_line(sock, {"role": "extension", "browser": os.environ.get("CHROME_VERSION", "")})
    recv_line(sock)
    return sock


def main() -> int:
    ensure_daemon()
    try:
        daemon = _connect()
    except OSError as exc:
        sys.stderr.write(f"pagouse-nm: {exc}\n")
        return 1
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    leftover = bytearray()
    try:
        while True:
            readable, _, _ = select.select([stdin, daemon], [], [])
            if stdin in readable:
                msg = nm_read(stdin)
                if msg is None:
                    break
                send_line(daemon, msg)
            if daemon in readable:
                chunk = daemon.recv(65536)
                if not chunk:
                    break
                leftover.extend(chunk)
                while b"\n" in leftover:
                    line, leftover = leftover.split(b"\n", 1)
                    if not line.strip():
                        continue
                    import json

                    payload = json.loads(bytes(line).decode())
                    if isinstance(payload, dict):
                        stdout.write(nm_pack(payload))
                        stdout.flush()
    except (OSError, ValueError):
        return 1
    finally:
        daemon.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
