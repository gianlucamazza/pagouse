"""Page snapshots. The extension maps tabs and AX nodes into these types."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj


@dataclass(frozen=True)
class Check:
    id: str
    ok: bool
    detail: str
    blocker: bool = False


@dataclass(frozen=True)
class Tab:
    id: int
    url: str
    title: str
    active: bool
    origin: str
