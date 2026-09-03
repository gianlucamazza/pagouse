"""Owner-only runtime paths for the managed browser session and artifacts."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path


def runtime_dir() -> Path:
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
    path = base / "pagouse"
    path.mkdir(mode=0o700, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(path, 0o700)
    return path
