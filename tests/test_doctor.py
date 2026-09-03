from __future__ import annotations

from pagouse.doctor import run_doctor
from pagouse.hosts.cli import main


def test_doctor_without_daemon_is_not_ready() -> None:
    report = run_doctor()
    assert report["ready"] is False
    assert "webdriver_bidi" in report["blockers"]
    assert report["session"]["active"] is False


def test_json_doctor_envelope(capsys: object) -> None:
    import json

    code = main(["--json", "doctor"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert payload["ok"] is True
    assert payload["action"] == "doctor"
    assert payload["ready"] is False
    assert payload["schema"] == 2
