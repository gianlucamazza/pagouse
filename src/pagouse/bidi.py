"""Small, synchronous WebDriver BiDi runtime for an isolated Chromium.

The runtime deliberately owns the browser process.  CDP is not used here:
the protocol boundary is kept in :mod:`pagouse.cdp` for browser capabilities
which WebDriver BiDi does not standardise yet.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import suppress
from pathlib import Path
from typing import Any

from pagouse.errors import (
    BadConfig,
    ContextNotFound,
    IpcFailed,
    NoSession,
    NoTab,
    SessionRecoveryFailed,
    SessionStartFailed,
    StaleMetadata,
    WebDriverError,
    WebDriverUnavailable,
)
from pagouse.paths import state_path, trusted_profile_dir

try:
    import websocket
except ImportError:  # pragma: no cover - exercised by doctor in a minimal install
    websocket = None  # type: ignore[assignment]


_MANAGED_BROWSER_CLASS = "pagouse-browser"


def _chromium_options(*, headless: bool, profile_mode: str) -> list[str]:
    options = [
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-search-engine-choice-screen",
        "--remote-allow-origins=*",
        f"--class={_MANAGED_BROWSER_CLASS}",
    ]
    if headless and profile_mode != "trusted":
        options.append("--headless=new")
    return options


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _json_request(
    url: str, method: str = "GET", body: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise IpcFailed(f"webdriver endpoint unavailable: {exc}") from exc


class BiDiClient:
    """Request/response WebDriver BiDi client with strict command matching."""

    def __init__(self, websocket_url: str) -> None:
        if websocket is None:
            raise BadConfig("install the websocket-client package")
        self._socket = websocket.create_connection(websocket_url, timeout=8)
        self._counter = 0
        self._lock = threading.Lock()

    def command(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            self._counter += 1
            command_id = self._counter
            self._socket.send(
                json.dumps({"id": command_id, "method": method, "params": params or {}})
            )
            while True:
                raw = self._socket.recv()
                if not raw:
                    raise IpcFailed("WebDriver BiDi connection closed")
                message = json.loads(raw)
                if message.get("id") != command_id:
                    continue
                if message.get("type") == "error":
                    value = message.get("message") or message.get("error") or "BiDi command failed"
                    raise WebDriverError(str(value))
                return message.get("result") or {}

    def close(self) -> None:
        self._socket.close()

    def wait_event(self, event_name: str, timeout_ms: int) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_ms / 1000
        self._socket.settimeout(max(0.1, timeout_ms / 1000))
        while time.monotonic() < deadline:
            try:
                raw = self._socket.recv()
            except Exception as exc:
                raise IpcFailed(f"event wait failed: {exc}") from exc
            if not raw:
                raise IpcFailed("WebDriver BiDi connection closed")
            message = json.loads(raw)
            if message.get("type") == "event" and message.get("method") == event_name:
                return message
        raise IpcFailed(f"event wait timed out after {timeout_ms}ms")


class BrowserSession:
    """Owned Chromium session.  A process is never attached implicitly."""

    def __init__(self) -> None:
        self._state_path = state_path()
        self.driver: subprocess.Popen[str] | None = None
        self.driver_pid = 0
        self.driver_port = 0
        self.client: BiDiClient | None = None
        self._websocket_url = ""
        self.session_id = ""
        self.profile: Path | None = None
        self.profile_mode = "isolated"
        self.debugger_address = ""
        self._contexts: list[str] = []
        self._refs: dict[str, int] = {}
        self._recovery_error: SessionRecoveryFailed | None = None
        self._restore()

    @property
    def active(self) -> bool:
        if self.client is None:
            return False
        if self.driver is not None:
            return self.driver.poll() is None
        if not self.driver_pid:
            return False
        try:
            os.kill(self.driver_pid, 0)
        except OSError:
            return False
        return True

    def start(self, *, headless: bool = True, mode: str = "isolated") -> dict[str, Any]:
        if self.active:
            return self.doctor()
        if mode not in {"isolated", "trusted"}:
            raise BadConfig("browser mode must be 'isolated' or 'trusted'")
        chromedriver = os.environ.get("PAGOUSE_CHROMEDRIVER") or shutil.which("chromedriver")
        chromium = os.environ.get("PAGOUSE_CHROMIUM") or shutil.which("chromium")
        if not chromedriver or not chromium:
            raise WebDriverUnavailable("chromium and chromedriver are required")
        self.profile_mode = mode
        self.profile = (
            Path(tempfile.mkdtemp(prefix="pagouse-chromium-"))
            if mode == "isolated"
            else trusted_profile_dir()
        )
        port = _free_port()
        self.driver = subprocess.Popen(
            [chromedriver, f"--port={port}", "--bind-address=127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self.driver_pid = self.driver.pid
        self.driver_port = port
        try:
            options = _chromium_options(headless=headless, profile_mode=mode)
            response = _json_request(
                f"http://127.0.0.1:{port}/session",
                "POST",
                {
                    "capabilities": {
                        "alwaysMatch": {
                            "browserName": "chrome",
                            "webSocketUrl": True,
                            "goog:chromeOptions": {
                                "binary": chromium,
                                "args": [*options, f"--user-data-dir={self.profile}"],
                            },
                        }
                    }
                },
            )
            value = response.get("value") or {}
            capabilities = value.get("capabilities") or {}
            websocket_url = capabilities.get("webSocketUrl")
            if not websocket_url:
                raise SessionStartFailed("ChromeDriver did not expose a WebDriver BiDi endpoint")
            self.session_id = str(value.get("sessionId") or response.get("sessionId") or "")
            self.debugger_address = str(
                (capabilities.get("goog:chromeOptions") or {}).get("debuggerAddress") or ""
            )
            self.client = BiDiClient(str(websocket_url))
            self._websocket_url = str(websocket_url)
            self._persist()
            tree = self.client.command("browsingContext.getTree")
            self._contexts = [str(item["context"]) for item in tree.get("contexts", [])]
            return self.doctor()
        except Exception as exc:
            self.stop()
            if isinstance(
                exc, (NoSession, WebDriverError, WebDriverUnavailable, SessionStartFailed)
            ):
                raise
            raise SessionStartFailed(str(exc)) from exc

    def stop(self) -> bool:
        was_active = self.active
        profile = self.profile
        if self.client is not None:
            self.client.close()
        self.client = None
        self._websocket_url = ""
        if self.session_id and self.driver_port:
            with suppress(IpcFailed):
                _json_request(
                    f"http://127.0.0.1:{self.driver_port}/session/{self.session_id}", "DELETE"
                )
        if self.driver is not None:
            self.driver.terminate()
            try:
                self.driver.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.driver.kill()
                self.driver.wait()
        elif self.driver_pid:
            with suppress(OSError):
                os.kill(self.driver_pid, signal.SIGTERM)
        self.driver = None
        if self.profile is not None and self.profile_mode == "isolated":
            shutil.rmtree(self.profile, ignore_errors=True)
        if profile is not None:
            self._kill_profile_processes(profile)
        self.profile = None
        self.profile_mode = "isolated"
        self.debugger_address = ""
        self.session_id = ""
        self._contexts = []
        self.driver_pid = 0
        self.driver_port = 0
        self._state_path.unlink(missing_ok=True)
        return was_active

    @staticmethod
    def _kill_profile_processes(profile: Path) -> None:
        """Kill only Chromium processes using this exact temporary profile."""
        marker = f"--user-data-dir={profile}"
        pids: list[int] = []
        for entry in Path("/proc").glob("[0-9]*"):
            try:
                command = b" ".join((entry / "cmdline").read_bytes().split(b"\0"))
            except OSError:
                continue
            if marker.encode() in command:
                with suppress(ValueError):
                    pids.append(int(entry.name))
        for pid in pids:
            with suppress(OSError):
                os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 2
        while pids and time.monotonic() < deadline:
            alive = []
            for pid in pids:
                try:
                    os.kill(pid, 0)
                except OSError:
                    continue
                alive.append(pid)
            if not alive:
                return
            pids = alive
            time.sleep(0.05)
        for pid in pids:
            with suppress(OSError):
                os.kill(pid, signal.SIGKILL)

    def _persist(self) -> None:
        payload = {
            "schema": 1,
            "driver_pid": self.driver_pid,
            "driver_port": self.driver_port,
            "session_id": self.session_id,
            "websocket_url": self._websocket_url,
            "profile": str(self.profile) if self.profile else "",
            "profile_mode": self.profile_mode,
            "debugger_address": self.debugger_address,
            "refs": self._refs,
            "updated_at": time.time(),
        }
        temporary = self._state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, self._state_path)

    def _restore(self) -> None:
        self.client = None
        self._recovery_error = None
        try:
            state = json.loads(self._state_path.read_text(encoding="utf-8"))
            if state.get("schema") != 1:
                raise StaleMetadata("unsupported managed browser metadata schema")
            self.driver_pid = int(state["driver_pid"])
            self.driver_port = int(state["driver_port"])
            self.session_id = str(state["session_id"])
            self.profile = Path(state["profile"]) if state.get("profile") else None
            self.profile_mode = str(state.get("profile_mode") or "isolated")
            if self.profile_mode not in {"isolated", "trusted"}:
                raise StaleMetadata("unsupported browser profile mode")
            self.debugger_address = str(state.get("debugger_address") or "")
            self._refs = {str(key): int(value) for key, value in (state.get("refs") or {}).items()}
            if self.driver_pid and self._pid_alive():
                self._websocket_url = str(state["websocket_url"])
                self.client = BiDiClient(self._websocket_url)
                self._contexts = [str(item["context"]) for item in self.contexts()]
            else:
                self._state_path.unlink(missing_ok=True)
        except (OSError, KeyError, TypeError, ValueError, IpcFailed, StaleMetadata) as exc:
            self.client = None
            self._state_path.unlink(missing_ok=True)
            if isinstance(exc, IpcFailed):
                self._recovery_error = SessionRecoveryFailed(str(exc))
        except Exception as exc:
            # A dead WebDriver endpoint can reject the WebSocket handshake with
            # a library-specific exception (for example HTTP 400). Treat that
            # as stale owner metadata so every CLI command remains usable.
            if websocket is None or not isinstance(exc, websocket.WebSocketException):
                raise
            self.client = None
            self._state_path.unlink(missing_ok=True)
            self._recovery_error = SessionRecoveryFailed(
                "managed browser session metadata is no longer valid"
            )

    def reload(self) -> None:
        """Reload owner metadata after another process starts the service."""
        self.client = None
        self.driver = None
        self.driver_pid = 0
        self.driver_port = 0
        self.session_id = ""
        self.profile = None
        self.profile_mode = "isolated"
        self.debugger_address = ""
        self._websocket_url = ""
        self._contexts = []
        self._refs = {}
        self._restore()

    def _pid_alive(self) -> bool:
        if not self.driver_pid:
            return False
        try:
            os.kill(self.driver_pid, 0)
        except OSError:
            return False
        return True

    def _require(self) -> BiDiClient:
        if self.client is None or not self.active:
            raise NoSession("no managed Chromium session")
        return self.client

    def doctor(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "session_id": self.session_id,
            "contexts": len(self._contexts),
            "profile_isolated": self.profile is not None or self.active,
            "profile_mode": self.profile_mode,
            "profile_persistent": self.profile_mode == "trusted",
            "trusted_profile_isolated": self.profile_mode == "trusted",
        }

    def contexts(self) -> list[dict[str, Any]]:
        result = self._require().command("browsingContext.getTree")
        self._contexts = [str(item["context"]) for item in result.get("contexts", [])]
        return result.get("contexts", [])

    def current_context(self) -> str:
        contexts = self.contexts()
        if not contexts:
            raise NoTab(None)
        return str(contexts[0]["context"])

    def set_refs(self, refs: dict[str, int]) -> None:
        self._refs = dict(refs)
        if self.client is not None:
            self._persist()

    def _point(self, ref: str) -> tuple[float, float]:
        from pagouse.cdp import command
        from pagouse.errors import StaleRef

        node = self._refs.get(ref)
        if not node or not self.debugger_address:
            raise StaleRef(ref)
        result = command(self.debugger_address, "DOM.getBoxModel", {"backendNodeId": node})
        quad = (result.get("model") or {}).get("content") or []
        if len(quad) < 8:
            raise StaleRef(ref)
        return (sum(quad[0::2]) / 4, sum(quad[1::2]) / 4)

    def pointer(self, ref: str, context: str | None = None) -> dict[str, Any]:
        context = context or self.current_context()
        x, y = self._point(ref)
        return self._require().command(
            "input.performActions",
            {
                "context": context,
                "actions": [
                    {
                        "type": "pointer",
                        "id": "pagouse-pointer",
                        "actions": [
                            {
                                "type": "pointerMove",
                                "x": round(x),
                                "y": round(y),
                                "origin": "viewport",
                            },
                            {"type": "pointerDown", "button": 0},
                            {"type": "pointerUp", "button": 0},
                        ],
                    }
                ],
            },
        )

    def keys(self, text: str, context: str | None = None) -> dict[str, Any]:
        context = context or self.current_context()
        actions: list[dict[str, Any]] = []
        for char in text:
            actions.extend(({"type": "keyDown", "value": char}, {"type": "keyUp", "value": char}))
        return self._require().command(
            "input.performActions",
            {
                "context": context,
                "actions": [{"type": "key", "id": "pagouse-key", "actions": actions}],
            },
        )

    def key_combo(self, combo: str, context: str | None = None) -> dict[str, Any]:
        context = context or self.current_context()
        parts = [part.strip().lower() for part in combo.split("+") if part.strip()]
        names = {
            "ctrl": "\ue009",
            "control": "\ue009",
            "shift": "\ue008",
            "alt": "\ue00a",
            "enter": "\ue007",
            "tab": "\ue004",
            "escape": "\ue00c",
            "esc": "\ue00c",
        }
        if not parts:
            raise WebDriverError("empty key combination")
        modifiers = [names[item] for item in parts[:-1] if item in names]
        key = names.get(parts[-1], parts[-1])
        actions = [{"type": "keyDown", "value": item} for item in modifiers]
        actions.extend(({"type": "keyDown", "value": key}, {"type": "keyUp", "value": key}))
        actions.extend({"type": "keyUp", "value": item} for item in reversed(modifiers))
        return self._require().command(
            "input.performActions",
            {
                "context": context,
                "actions": [{"type": "key", "id": "pagouse-key", "actions": actions}],
            },
        )

    def scroll(self, ref: str, context: str | None = None) -> dict[str, Any]:
        context = context or self.current_context()
        x, y = self._point(ref)
        return self._require().command(
            "input.performActions",
            {
                "context": context,
                "actions": [
                    {
                        "type": "wheel",
                        "id": "pagouse-wheel",
                        "actions": [
                            {
                                "type": "scroll",
                                "x": round(x),
                                "y": round(y),
                                "deltaX": 0,
                                "deltaY": 600,
                            },
                        ],
                    }
                ],
            },
        )

    def navigate(self, context: str, url: str) -> dict[str, Any]:
        if context not in self._contexts:
            raise ContextNotFound(context)
        return self._require().command(
            "browsingContext.navigate", {"context": context, "url": url, "wait": "complete"}
        )

    def wait_event(
        self, event_name: str, timeout_ms: int, context: str | None = None
    ) -> dict[str, Any]:
        if timeout_ms <= 0:
            raise WebDriverError("timeout_ms must be positive")
        client = self._require()
        params: dict[str, Any] = {"events": [event_name]}
        if context:
            params["contexts"] = [context]
        client.command("session.subscribe", params)
        return client.wait_event(event_name, timeout_ms)


_session = BrowserSession()


def session() -> BrowserSession:
    return _session
