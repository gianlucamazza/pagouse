from __future__ import annotations

from unittest.mock import Mock

import pytest

from pagouse import bidi
from pagouse.errors import IpcFailed, SessionStartFailed


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    clock = Mock(now=0.0)
    monkeypatch.setattr(bidi.time, "monotonic", lambda: clock.now)

    def advance(seconds: float) -> None:
        clock.now += seconds

    monkeypatch.setattr(bidi.time, "sleep", advance)
    return clock


def test_driver_waits_through_connection_refusal_and_not_ready(
    monkeypatch: pytest.MonkeyPatch, clock: Mock
) -> None:
    browser = bidi.BrowserSession()
    browser.driver = Mock(poll=Mock(return_value=None))
    browser.driver_port = 4321
    request = Mock(
        side_effect=[IpcFailed("refused"), {"value": {"ready": False}}, {"value": {"ready": True}}]
    )
    monkeypatch.setattr(bidi, "_json_request", request)

    browser._wait_for_driver()

    assert request.call_count == 3
    assert clock.now == pytest.approx(0.1)
    for call in request.call_args_list:
        assert call.args == ("http://127.0.0.1:4321/status",)
        assert call.kwargs["timeout"] <= 0.5


def test_driver_exit_does_not_wait_for_timeout(
    monkeypatch: pytest.MonkeyPatch, clock: Mock
) -> None:
    browser = bidi.BrowserSession()
    browser.driver = Mock(poll=Mock(return_value=1))
    request = Mock()
    monkeypatch.setattr(bidi, "_json_request", request)

    with pytest.raises(SessionStartFailed, match="exited"):
        browser._wait_for_driver()

    request.assert_not_called()
    assert clock.now == 0


def test_driver_readiness_timeout_is_bounded(monkeypatch: pytest.MonkeyPatch, clock: Mock) -> None:
    browser = bidi.BrowserSession()
    browser.driver = Mock(poll=Mock(return_value=None))
    monkeypatch.setattr(bidi, "_json_request", Mock(side_effect=IpcFailed("refused")))

    with pytest.raises(SessionStartFailed, match=r"within 0\.2 seconds"):
        browser._wait_for_driver(timeout=0.2)

    assert clock.now == pytest.approx(0.2)


def test_startup_failure_reaps_driver_and_removes_owned_profile(
    monkeypatch: pytest.MonkeyPatch, clock: Mock
) -> None:
    browser = bidi.BrowserSession()
    driver = Mock(pid=123456, poll=Mock(return_value=None))
    monkeypatch.setattr(bidi.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(bidi, "_free_port", lambda: 4321)
    monkeypatch.setattr(bidi.subprocess, "Popen", Mock(return_value=driver))
    monkeypatch.setattr(browser, "_kill_profile_processes", Mock())
    monkeypatch.setattr(bidi, "_json_request", Mock(side_effect=IpcFailed("refused")))

    with pytest.raises(SessionStartFailed, match="did not become ready"):
        browser.start()

    driver.terminate.assert_called_once()
    driver.wait.assert_called_once_with(timeout=3)
    profile = browser._kill_profile_processes.call_args.args[0]
    assert not profile.exists()
    assert browser.profile is None
    assert browser.driver is None
    assert browser.driver_pid == 0
