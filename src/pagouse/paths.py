"""Runtime and native-messaging locations. Owner-only on the runtime dir."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

HOST_NAME = "it.gianlucamazza.pagouse"
SOCKET_NAME = "pagoused.sock"


def runtime_dir() -> Path:
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
    path = base / "pagouse"
    path.mkdir(mode=0o700, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(path, 0o700)
    return path


def socket_path() -> Path:
    return runtime_dir() / SOCKET_NAME


_BROWSER_DIRS = (
    "chromium",
    "google-chrome",
    "google-chrome-beta",
    "BraveSoftware/Brave-Browser",
    "microsoft-edge",
    "microsoft-edge-beta",
    "vivaldi",
    "thorium",
)

# /proc comm → config directory name under XDG_CONFIG_HOME.
_COMM_TO_DIR = {
    "chromium": "chromium",
    "chrome": "google-chrome",
    "brave": "BraveSoftware/Brave-Browser",
    "vivaldi": "vivaldi",
    "msedge": "microsoft-edge",
}


def native_host_dirs() -> list[Path]:
    """Chromium-family NativeMessagingHosts directories that may exist."""
    home = Path.home()
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    running = _running_browser_dirs()
    names = running + [n for n in _BROWSER_DIRS if n not in running]
    return [xdg / name / "NativeMessagingHosts" for name in names] + [
        home / ".config" / name / "NativeMessagingHosts" for name in names
    ]


def _running_browser_dirs() -> list[str]:
    found: list[str] = []
    for comm in Path("/proc").glob("*/comm"):
        try:
            name = comm.read_text().strip()
        except OSError:
            continue
        mapped = _COMM_TO_DIR.get(name)
        if mapped and mapped not in found:
            found.append(mapped)
    return found


def native_host_manifests() -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for directory in native_host_dirs():
        path = directory / f"{HOST_NAME}.json"
        resolved = path.resolve() if path.exists() else path
        if resolved in seen:
            continue
        seen.add(resolved)
        found.append(path)
    return found


def preferred_host_manifest() -> Path | None:
    for path in native_host_manifests():
        if path.is_file():
            return path
    return None
