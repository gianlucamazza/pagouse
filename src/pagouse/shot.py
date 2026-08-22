"""Write a viewport capture to $XDG_RUNTIME_DIR and optionally fit it."""

from __future__ import annotations

import base64
import contextlib
import re
import shutil
import subprocess
import time
from pathlib import Path

from pagouse.contract import DEFAULT_FIT
from pagouse.paths import runtime_dir

_DATA_URL = re.compile(r"^data:image/(png|jpeg);base64,(.+)$", re.DOTALL | re.IGNORECASE)


def fit_scale(width: int, height: int, long_edge: int) -> tuple[float, int, int]:
    if long_edge <= 0 or width <= 0 or height <= 0:
        return 1.0, width, height
    current = max(width, height)
    if current <= long_edge:
        return 1.0, width, height
    factor = long_edge / current
    return factor, max(1, round(width * factor)), max(1, round(height * factor))


def apply_fit(
    path: Path, width: int, height: int, scale: float, long_edge: int
) -> tuple[float, int, int, bool]:
    factor, new_w, new_h = fit_scale(width, height, long_edge)
    if factor == 1.0:
        return scale, width, height, False
    magick = shutil.which("magick")
    if not magick:
        return scale, width, height, True
    proc = subprocess.run(
        [magick, str(path), "-resize", f"{long_edge}x{long_edge}>", str(path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if proc.returncode != 0:
        return scale, width, height, True
    return scale * factor, new_w, new_h, False


def _gc_old_shots(directory: Path, *, max_age_s: int = 1800) -> None:
    now = time.time()
    for path in directory.glob("shot-*"):
        try:
            if now - path.stat().st_mtime > max_age_s:
                path.unlink()
        except OSError:
            continue


def save_data_url(
    data_url: str,
    *,
    width: int,
    height: int,
    fit: int = DEFAULT_FIT,
) -> dict[str, object]:
    match = _DATA_URL.match(data_url.strip())
    if not match:
        raise ValueError("shot payload is not a png/jpeg data URL")
    kind, blob = match.group(1).lower(), match.group(2)
    ext = "jpg" if kind == "jpeg" else "png"
    dest_dir = runtime_dir()
    _gc_old_shots(dest_dir)
    dest = dest_dir / f"shot-{time.time_ns()}.{ext}"
    dest.write_bytes(base64.b64decode(blob))
    with contextlib.suppress(OSError):
        dest.chmod(0o600)
    scale, out_w, out_h, fit_skipped = apply_fit(dest, width, height, 1.0, fit)
    result: dict[str, object] = {"path": str(dest), "width": out_w, "height": out_h, "scale": scale}
    if fit_skipped:
        result["fit_skipped"] = True
    return result
