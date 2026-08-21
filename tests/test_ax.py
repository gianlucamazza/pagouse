from __future__ import annotations

import json
from pathlib import Path

from pagouse.ax import count_refs, format_tree

ROOT = Path(__file__).resolve().parents[1]


def test_login_fixture_formats_and_redacts() -> None:
    raw = json.loads((ROOT / "testdata" / "ax" / "login.json").read_text())
    tree = format_tree(raw)
    assert "[ref_1]" in tree
    assert 'textbox "Email" [ref_2]' in tree
    assert "placeholder=you@example.com" in tree
    assert "[redacted]" in tree
    assert "hunter2" not in tree
    assert 'button "Sign in" [ref_4]' in tree
    assert "href=/reset" in tree
    assert count_refs(raw) == 5
