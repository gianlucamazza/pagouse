"""Format an accessibility node list into the snapshot tree text.

The live walker lives in extension/content/ax.js. This module is the
hermetic formatter the tests pin, so the contract does not drift.
"""

from __future__ import annotations

from typing import Any

MAX_NAME = 80


def format_name(name: str) -> str:
    collapsed = " ".join(name.split())
    if len(collapsed) > MAX_NAME:
        collapsed = collapsed[: MAX_NAME - 1] + "…"
    return collapsed


def format_node(node: dict[str, Any], indent: int = 0) -> list[str]:
    role = str(node.get("role") or "generic")
    name = format_name(str(node.get("name") or ""))
    ref = node.get("ref")
    parts = ["  " * indent + role]
    if name:
        parts.append(f'"{name}"')
    if ref:
        parts.append(f"[{ref}]")
    extras: list[str] = []
    href = node.get("href")
    if href:
        extras.append(f"href={href}")
    node_type = node.get("type")
    if node_type:
        extras.append(f"type={node_type}")
    if node.get("placeholder"):
        extras.append(f"placeholder={node['placeholder']}")
    if node.get("redacted"):
        extras.append("[redacted]")
    if node.get("checked") is True:
        extras.append("checked")
    if node.get("value") not in (None, "") and not node.get("redacted"):
        extras.append(f"value={node['value']}")
    if extras:
        parts.append(" ".join(extras))
    lines = [" ".join(parts)]
    for child in node.get("children") or []:
        if isinstance(child, dict):
            lines.extend(format_node(child, indent + 1))
    return lines


def format_tree(root: dict[str, Any]) -> str:
    return "\n".join(format_node(root)) + "\n"


def count_refs(node: dict[str, Any]) -> int:
    n = 1 if node.get("ref") else 0
    for child in node.get("children") or []:
        if isinstance(child, dict):
            n += count_refs(child)
    return n
