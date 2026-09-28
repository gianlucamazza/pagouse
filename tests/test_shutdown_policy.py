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
