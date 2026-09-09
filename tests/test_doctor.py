from __future__ import annotations

from types import SimpleNamespace

import pytest

from pagouse.doctor import run_doctor
from pagouse.hosts.cli import main


def _mock_disconnected_session(monkeypatch: pytest.MonkeyPatch) -> None:
    state = {
        "active": False,
        "session_id": None,
        "contexts": 0,
        "profile_isolated": True,
    }
    monkeypatch.setattr(
        "pagouse.doctor.session",
        lambda: SimpleNamespace(doctor=lambda: state),
    )


def test_doctor_without_daemon_is_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_disconnected_session(monkeypatch)
    report = run_doctor()
    assert report["ready"] is False
    assert "webdriver_bidi" in report["blockers"]
    assert report["session"]["active"] is False


def test_json_doctor_envelope(capsys: object, monkeypatch: pytest.MonkeyPatch) -> None:
    import json

    _mock_disconnected_session(monkeypatch)
    code = main(["--json", "doctor"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert payload["ok"] is True
    assert payload["action"] == "doctor"
    assert payload["ready"] is False
    assert payload["schema"] == 2
