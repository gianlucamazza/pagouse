from __future__ import annotations

import pytest

from pagouse.errors import BadArg, WaitTimeout
from pagouse.observe import wait


def test_wait_requires_a_condition() -> None:
    with pytest.raises(BadArg):
        wait(tab_id=1, timeout_ms=10)


def test_wait_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pagouse.observe.tabs",
        lambda: {"tabs": [{"id": 1, "url": "https://example.com/"}], "active": 1},
    )
    monkeypatch.setattr(
        "pagouse.observe.snapshot",
        lambda *_a, **_k: {
            "tab_id": 1,
            "url": "https://example.com/",
            "tree": "RootWebArea [ref_f0_1]\n",
        },
    )
    with pytest.raises(WaitTimeout):
        wait(tab_id=1, ref="ref_f0_99", timeout_ms=50)


def test_wait_matches_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pagouse.observe.snapshot",
        lambda *_a, **_k: {
            "tab_id": 7,
            "url": "https://example.com/",
            "tree": 'button "Go" [ref_f0_2]\n',
        },
    )
    out = wait(tab_id=7, ref="ref_f0_2", timeout_ms=500)
    assert out["matched"] == "ref"
    assert out["tab_id"] == 7
