from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "pagouse"


def test_core_does_not_import_a_seat_adapter() -> None:
    import re

    leaked: list[str] = []
    pattern = re.compile(r"^\s*(from|import)\s+mangouse", re.MULTILINE)
    for path in SRC.rglob("*.py"):
        if pattern.search(path.read_text()):
            leaked.append(str(path.relative_to(ROOT)))
    assert not leaked, f"seat-adapter import leaked into page-agent core: {leaked}"


def test_core_does_not_name_compositor_ipc() -> None:
    banned = ("hyprctl", "mmsg", "swaymsg")
    leaked: list[str] = []
    for path in SRC.rglob("*.py"):
        text = path.read_text()
        for token in banned:
            if token in text:
                leaked.append(f"{path.relative_to(ROOT)}:{token}")
    assert not leaked
