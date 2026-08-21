from __future__ import annotations

import threading
import time

from pagouse.daemon import listen, stop
from pagouse.errors import NoSession
from pagouse.session import call


def test_ping_without_extension() -> None:
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            reply = call("ping")
            break
        except NoSession:
            time.sleep(0.05)
    else:
        raise AssertionError("daemon did not start")
    assert reply["ok"] is True
    assert reply["extension"] is False
    assert stop() is True
