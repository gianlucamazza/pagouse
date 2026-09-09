from __future__ import annotations

from pagouse.bidi import _chromium_options


def test_managed_chromium_uses_a_dedicated_desktop_identity() -> None:
    options = _chromium_options(headless=False, profile_mode="isolated")

    assert "--class=pagouse-browser" in options
    assert "--headless=new" not in options


def test_isolated_chromium_can_run_headless() -> None:
    options = _chromium_options(headless=True, profile_mode="isolated")

    assert "--headless=new" in options


def test_trusted_chromium_is_always_headed() -> None:
    options = _chromium_options(headless=True, profile_mode="trusted")

    assert "--class=pagouse-browser" in options
    assert "--headless=new" not in options
