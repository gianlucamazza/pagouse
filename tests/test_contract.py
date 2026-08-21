from __future__ import annotations

import json

from pagouse.contract import SCHEMA, envelope
from pagouse.hosts.cli import main


def test_envelope_shape() -> None:
    ok = envelope(ok=True, action="tabs", data={"tabs": []})
    assert ok["schema"] == SCHEMA
    assert ok["ok"] is True
    assert ok["action"] == "tabs"
    assert "error" not in ok


def test_json_usage_is_envelope(capsys: object) -> None:
    code = main(["--json", "click"])
    assert code == 2
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert payload["error"] == "usage"
    assert payload["schema"] == 1
    assert payload["action"] == "usage"
