"""CLI surface and version stay documented."""

from __future__ import annotations

from pathlib import Path

from pagouse import __version__
from pagouse.config import parse_config
from pagouse.hosts.cli import build_parser

ROOT = Path(__file__).resolve().parents[1]


def _shipped_text_files() -> list[Path]:
    skip = {
        ".venv",
        ".git",
        "node_modules",
        "tests",
        "__pycache__",
        ".ruff_cache",
        ".pytest_cache",
    }
    suffixes = {".md", ".py", ".toml", ".json"}
    out: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in skip for part in path.relative_to(ROOT).parts):
            continue
        out.append(path)
    return out


def test_shipped_texts_do_not_name_a_seat_adapter() -> None:
    """This repo's playbook and source do not document a sibling seat CLI."""
    hits: list[str] = []
    for path in _shipped_text_files():
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if "mangouse" in line.lower():
                hits.append(f"{path.relative_to(ROOT)}:{lineno}")
    assert not hits, f"seat adapter named in shipped texts: {hits}"


def test_version_is_in_the_changelog() -> None:
    assert f"## [{__version__}]" in (ROOT / "CHANGELOG.md").read_text()


def _markdown_files() -> list[Path]:
    skip = {".venv", ".git", "node_modules"}
    return [
        path
        for path in ROOT.rglob("*.md")
        if not any(part in skip for part in path.relative_to(ROOT).parts)
    ]


def test_no_document_hardcodes_a_version() -> None:
    import re

    pattern = re.compile(r"(?<![\d.])\d+\.\d+\.\d+(?![\d.])")
    allowed = {__version__}
    stale: list[str] = []
    for path in _markdown_files():
        if path.name == "CHANGELOG.md":
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for found in pattern.findall(line):
                if found not in allowed:
                    rel = path.relative_to(ROOT)
                    stale.append(f"{rel}:{lineno} {found}")
    assert not stale, f"hardcoded versions in docs: {stale}"


def test_relative_links_resolve() -> None:
    import re

    link = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    broken: list[str] = []
    for path in _markdown_files():
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for target in link.findall(line):
                target = target.split("#", 1)[0].strip()
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                if not (path.parent / target).exists():
                    broken.append(f"{path.relative_to(ROOT)}:{lineno} -> {target}")
    assert not broken, f"broken relative links: {broken}"


def test_env_vars_are_documented() -> None:
    import re

    names: set[str] = set()
    for path in (ROOT / "src").rglob("*.py"):
        names |= set(re.findall(r"PAGOUSE_[A-Z_]+", path.read_text()))
    assert names, "no PAGOUSE_* env vars found in src/"
    docs = (ROOT / "docs" / "configuration.md").read_text()
    missing = sorted(n for n in names if n not in docs)
    assert not missing, f"undocumented env vars in docs/configuration.md: {missing}"


def test_cli_actions_are_documented() -> None:
    parser = build_parser()
    cmds = set()
    for action in parser._actions:
        if action.dest == "cmd" and action.choices:
            cmds = set(action.choices)
            break
    headless = (ROOT / "docs" / "json-contract.md").read_text()
    for name in cmds:
        assert f"`{name}`" in headless, f"{name} missing from docs/json-contract.md"


def test_example_config_keys_parse() -> None:
    import tomllib

    data = tomllib.loads((ROOT / "examples" / "config.toml").read_text())
    cfg = parse_config(data)
    assert cfg.allow_input is False


def _optstrings(parser) -> set[str]:
    out: set[str] = set()
    for action in parser._actions:
        for opt in action.option_strings:
            if opt not in {"-h", "--help"}:
                out.add(opt)
    return out


def test_cli_flags_are_documented() -> None:
    parser = build_parser()
    flags = _optstrings(parser)
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            for sub in choices.values():
                flags |= _optstrings(sub)
    tools = (ROOT / "docs" / "cli-reference.md").read_text()
    missing = sorted(f for f in flags if f not in tools)
    assert not missing, f"undocumented flags in docs/cli-reference.md: {missing}"


def test_error_codes_are_documented() -> None:
    import re

    body = (ROOT / "src" / "pagouse" / "errors.py").read_text()
    codes = set(re.findall(r'super\(\)\.__init__\(\s*"([a-z_]+)"', body))
    assert codes, "no error codes found in errors.py"
    headless = (ROOT / "docs" / "json-contract.md").read_text()
    missing = sorted(c for c in codes if f"| `{c}` |" not in headless)
    assert not missing, f"undocumented error codes in docs/json-contract.md: {missing}"


def _mcp_tool_names() -> set[str]:
    import ast

    tree = ast.parse((ROOT / "src" / "pagouse" / "hosts" / "mcp.py").read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            func = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(func, ast.Attribute) and func.attr == "tool":
                names.add(node.name)
    return names


def test_mcp_tool_list_matches_docs() -> None:
    import re

    tools = _mcp_tool_names()
    assert tools, "no @server.tool functions found in hosts/mcp.py"
    for rel, marker in (
        ("docs/cli-reference.md", "The MCP extra exposes"),
        ("docs/security-model.md", "The extra exposes"),
    ):
        text = (ROOT / rel).read_text()
        assert marker in text, f"{rel} lost its MCP tool sentence"
        window = text.split(marker, 1)[1].split(".")[0]
        listed = set(re.findall(r"`([a-z_]+)`", window))
        assert listed == tools, f"{rel} lists {sorted(listed)}, MCP exposes {sorted(tools)}"


def test_doctor_keys_are_documented() -> None:
    from pagouse.doctor import run_doctor

    headless = (ROOT / "docs" / "json-contract.md").read_text()
    row = next(line for line in headless.splitlines() if line.startswith("| `doctor` |"))
    report = run_doctor()
    missing = sorted(k for k in report if f"`{k}`" not in row)
    assert not missing, f"doctor keys missing from docs/json-contract.md: {missing}"


def test_skill_mentions_the_gates() -> None:
    skill = (ROOT / "skills" / "pagouse" / "SKILL.md").read_text()
    assert '"schema": 2' in skill
    assert "stale_ref" in skill
    assert "--allow-input" in skill
    assert 'error: "usage"' in skill
    assert "click --ref" in skill
    assert "pagouse --json shot --tab ID" in skill
    assert "mangouse" not in skill
