"""Persistent user-level owner for the isolated Chromium session."""

from __future__ import annotations

import argparse
import fcntl
import signal
import time
from contextlib import suppress

from pagouse.bidi import session
from pagouse.paths import cleanup_runtime, lock_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pagouse-browserd")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args(argv)
    browser = session()
    stopping = False

    lock = lock_path().open("w", encoding="utf-8")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        return 0

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    cleanup_runtime()
    browser.start(headless=not args.headed)
    try:
        while not stopping:
            if not browser.active:
                break
            time.sleep(1)
    finally:
        browser.stop()
        cleanup_runtime()
        with suppress(OSError):
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()
    return 0
