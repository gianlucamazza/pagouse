"""Owner-only runtime paths for the managed browser session and artifacts."""

from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from pathlib import Path


def runtime_dir() -> Path:
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
    path = base / "pagouse"
    path.mkdir(mode=0o700, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(path, 0o700)
    return path


def state_path() -> Path:
    return runtime_dir() / "bidi-session.json"


def lock_path() -> Path:
    return runtime_dir() / "browser.lock"


def cleanup_runtime() -> int:
    """Remove only pagouse-owned legacy runtime artifacts."""
    removed = 0
    directory = runtime_dir()
    for path in (directory / "pagoused.sock", *directory.glob("shot-*")):
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue
        removed += 1
    for profile in Path(tempfile.gettempdir()).glob("pagouse-chromium-*"):
        if not profile.is_dir() or _profile_in_use(profile):
            continue
        shutil.rmtree(profile, ignore_errors=True)
        if not profile.exists():
            removed += 1
    return removed


def _profile_in_use(profile: Path) -> bool:
    marker = f"--user-data-dir={profile}".encode()
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            if marker in (entry / "cmdline").read_bytes():
                return True
        except OSError:
            continue
    return False
