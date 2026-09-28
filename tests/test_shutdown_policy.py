import signal
from pathlib import Path
from unittest.mock import Mock

import pytest

from pagouse import bidi


@pytest.mark.parametrize("mode", ["isolated", "trusted"])
def test_stop_cleans_processes_before_removing_profile(monkeypatch, tmp_path, mode):
    browser = bidi.BrowserSession()
    browser._state_path = tmp_path / "owner.json"
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "sentinel").write_text("preserve until processes are gone")
    browser.profile = profile
    browser.profile_mode = mode
    browser.driver = Mock()
    browser.driver_port = 4321
    browser.session_id = "test"
    events = []
    monkeypatch.setattr(bidi, "_json_request", lambda *a, **k: events.append("delete"))

    def cleanup(owned_profile):
        assert owned_profile == profile
        assert (profile / "sentinel").exists()
        assert events == ["delete"]
        assert browser.driver is None
        events.append("cleanup")

    monkeypatch.setattr(browser, "_kill_profile_processes", cleanup)
    browser.stop()
    assert events == ["delete", "cleanup"]
    assert profile.exists() == (mode == "trusted")
    assert browser.profile is None


def test_all_browser_modes_share_bounded_graceful_shutdown():
    install = Path(__file__).resolve().parents[1] / "install"
    for name in ("pagouse-browser", "pagouse-browser-headed", "pagouse-browser-trusted"):
        unit = (install / f"{name}.service").read_text()
        assert "KillMode=mixed\n" in unit
        assert "TimeoutStopSec=20s\n" in unit


def test_profile_cleanup_matches_whole_argv_not_prefix_or_shell_text(monkeypatch, tmp_path):
    profile = tmp_path / "owned"
    marker = f"--user-data-dir={profile}"
    entries = []
    for pid, args in (
        (101, ["chromium", marker]),
        (102, ["chromium", marker + "-other"]),
        (103, ["bash", "-c", "echo " + marker]),
    ):
        entry = tmp_path / str(pid)
        entry.mkdir()
        (entry / "cmdline").write_bytes(b"\0".join(a.encode() for a in args) + b"\0")
        entries.append(entry)
    original_glob = Path.glob
    monkeypatch.setattr(
        Path,
        "glob",
        lambda self, pattern: entries if self == Path("/proc") else original_glob(self, pattern),
    )
    signals = []

    def kill(pid, sig):
        if sig == 0:
            raise ProcessLookupError
        signals.append((pid, sig))

    monkeypatch.setattr(bidi.os, "kill", kill)
    bidi.BrowserSession._kill_profile_processes(profile)
    assert signals == [(101, signal.SIGTERM)]
