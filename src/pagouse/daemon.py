"""Long-lived router between CLI clients and the Chromium extension."""

from __future__ import annotations

import contextlib
import json
import os
import socket
import sys
import threading
from queue import Empty, Queue
from typing import Any

from pagouse.errors import PagouseError
from pagouse.ipc import send_line
from pagouse.log import logger
from pagouse.paths import socket_path

MUTATE_OPS = frozenset(
    {"click", "fill", "type", "key", "navigate", "tab_open", "tab_focus", "scroll"}
)
_FORWARD_TIMEOUT = 8.0
_CAPS_TIMEOUT = 1.5
_MAX_CONCURRENT = 16


class Hub:
    def __init__(self, max_concurrent: int = _MAX_CONCURRENT) -> None:
        self.lock = threading.Lock()
        self.semaphore = threading.Semaphore(max_concurrent)
        self.extension: socket.socket | None = None
        self.browser = ""
        self.pending: dict[int, Queue[dict[str, Any]]] = {}
        self.next_id = 1
        self.stopped = False

    def status(self) -> dict[str, Any]:
        with self.lock:
            connected = self.extension is not None
            browser = self.browser
        return {
            "ok": True,
            "op": "ping",
            "extension": connected,
            "browser": browser,
            "tabs": 0,
        }

    def capabilities(self) -> dict[str, Any]:
        """Ask the connected extension for version and site-access, briefly."""
        with self.lock:
            ext = self.extension
            if ext is None:
                return {"version": "", "all_urls": False}
            rid = self.next_id
            self.next_id += 1
            waiter: Queue[dict[str, Any]] = Queue()
            self.pending[rid] = waiter
        try:
            send_line(ext, {"op": "ping", "id": rid})
            reply = waiter.get(timeout=_CAPS_TIMEOUT)
        except (OSError, Empty):
            return {"version": "", "all_urls": False}
        finally:
            with self.lock:
                self.pending.pop(rid, None)
        return {
            "version": str(reply.get("version") or ""),
            "all_urls": bool(reply.get("all_urls")),
        }

    def _serve(self, conn: socket.socket) -> None:
        try:
            self.serve(conn)
        finally:
            self.semaphore.release()

    def serve(self, conn: socket.socket) -> None:
        reader = conn.makefile("r", encoding="utf-8")
        try:
            while True:
                line = reader.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line)
                except ValueError:
                    logger.debug("invalid json from client")
                    send_line(
                        conn,
                        {
                            "ok": False,
                            "error": "ipc_failed",
                            "message": "invalid json",
                        },
                    )
                    continue
                if not isinstance(msg, dict):
                    continue
                self.dispatch(conn, msg)
        except OSError:
            pass
        finally:
            with self.lock:
                if conn is self.extension:
                    self.extension = None
                    self.browser = ""
                    logger.info("extension disconnected")
            with contextlib.suppress(OSError):
                conn.close()

    def dispatch(self, conn: socket.socket, msg: dict[str, Any]) -> None:
        if msg.get("role") == "extension":
            with self.lock:
                self.extension = conn
                self.browser = str(msg.get("browser") or "")
            logger.info("extension connected (browser=%s)", self.browser)
            send_line(conn, {"ok": True, "op": "hello"})
            return
        with self.lock:
            is_ext = conn is self.extension
        if is_ext:
            rid = msg.get("id")
            with self.lock:
                waiter = self.pending.get(rid) if isinstance(rid, int) else None
            if waiter is not None:
                waiter.put(msg)
            return
        op = str(msg.get("op") or "")
        if op == "stop":
            send_line(conn, {"ok": True, "op": "stop", "stopped": True})
            self.stopped = True
            return
        if op in {"ping", "status"}:
            reply = self.status()
            reply.update(self.capabilities())
            send_line(conn, reply)
            return
        if op in {"wait_ref"}:
            logger.debug("observe op=%s", op)
        if op in MUTATE_OPS:
            logger.debug("mutate op=%s", op)
            try:
                self._gate_mutate(msg)
            except PagouseError as exc:
                logger.warning("mutate gate failed: %s", exc.message)
                send_line(
                    conn,
                    {
                        "ok": False,
                        "op": op,
                        "error": exc.code,
                        "message": exc.message,
                    },
                )
                return
        self.forward(conn, msg)

    def _gate_mutate(self, msg: dict[str, Any]) -> None:
        from pagouse.policy import require_origin
        from pagouse.safety import require_input

        require_input(cli_flag=bool(msg.get("allow_input")))
        url = str(msg.get("url") or msg.get("expected_origin") or "")
        if url:
            require_origin(url)

    def forward(self, conn: socket.socket, msg: dict[str, Any]) -> None:
        with self.lock:
            ext = self.extension
            if ext is None:
                send_line(
                    conn,
                    {
                        "ok": False,
                        "op": msg.get("op"),
                        "error": "no_session",
                        "message": "extension not connected",
                    },
                )
                return
            rid = self.next_id
            self.next_id += 1
            waiter: Queue[dict[str, Any]] = Queue()
            self.pending[rid] = waiter
        fwd = {k: v for k, v in msg.items() if k != "allow_input"}
        fwd["id"] = rid
        try:
            send_line(ext, fwd)
        except OSError as exc:
            with self.lock:
                self.pending.pop(rid, None)
            send_line(
                conn,
                {
                    "ok": False,
                    "op": msg.get("op"),
                    "error": "ipc_failed",
                    "message": str(exc),
                },
            )
            return
        try:
            reply = waiter.get(timeout=_FORWARD_TIMEOUT)
        except Empty:
            reply = {
                "ok": False,
                "op": msg.get("op"),
                "error": "ipc_failed",
                "message": "extension timed out",
            }
        finally:
            with self.lock:
                self.pending.pop(rid, None)
        reply.pop("id", None)
        send_line(conn, reply)


def listen(path: Any | None = None) -> int:
    target = path or socket_path()
    if target.exists():
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        probe.settimeout(0.2)
        try:
            probe.connect(str(target))
        except OSError:
            target.unlink(missing_ok=True)
        else:
            sys.stderr.write(f"pagoused already running at {target}\n")
            return 0
        finally:
            probe.close()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    old = os.umask(0o177)
    try:
        server.bind(str(target))
    finally:
        os.umask(old)
    with contextlib.suppress(OSError):
        os.chmod(target, 0o600)
    server.listen(16)
    server.settimeout(0.5)
    hub = Hub()
    try:
        while not hub.stopped:
            try:
                conn, _ = server.accept()
            except TimeoutError:
                continue
            conn.settimeout(None)
            hub.semaphore.acquire()
            threading.Thread(target=hub._serve, args=(conn,), daemon=True).start()
    finally:
        server.close()
        target.unlink(missing_ok=True)
    return 0


def stop() -> bool:
    from pagouse.errors import NoSession
    from pagouse.session import call

    try:
        call("stop")
    except (NoSession, OSError):
        path = socket_path()
        if path.exists():
            path.unlink(missing_ok=True)
            return True
        return False
    return True


def main() -> int:
    from pagouse.log import setup

    setup()
    if "--stop" in sys.argv:
        stopped = stop()
        sys.stdout.write(json.dumps({"ok": True, "stopped": stopped}) + "\n")
        return 0
    logger.info("pagoused listening on %s", socket_path())
    return listen()


if __name__ == "__main__":
    raise SystemExit(main())
