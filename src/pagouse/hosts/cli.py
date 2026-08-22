"""pagouse CLI. --json is the agent contract (see docs/json-contract.md)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Never

from pagouse import __version__
from pagouse.contract import DEFAULT_FIT
from pagouse.contract import envelope as _envelope
from pagouse.errors import PagouseError
from pagouse.log import setup

_EXIT_2 = frozenset({"readonly", "denied", "origin_changed", "bad_arg", "bad_config", "usage"})


def _print(payload: dict[str, Any], *, as_json: bool, human: str | None = None) -> int:
    if as_json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif human is not None:
        sys.stdout.write(human)
        if not human.endswith("\n"):
            sys.stdout.write("\n")
    else:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    if payload.get("ok"):
        return 0
    code = str(payload.get("error") or "")
    return 2 if code in _EXIT_2 else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    from pagouse.doctor import run_doctor

    report = run_doctor()
    payload = _envelope(ok=True, action="doctor", data=report)
    lines = [
        f"ready={report['ready']} observe={report['observe_ready']} "
        f"shot={report['shot_ready']} mutate={report['mutate_ready']}"
    ]
    if report["blockers"]:
        lines.append("blockers: " + ", ".join(report["blockers"]))
    for check in report["checks"]:
        mark = "ok" if check["ok"] else "FAIL"
        lines.append(f"  {check['id']}: {mark}  {check['detail']}")
    return _print(payload, as_json=args.json, human="\n".join(lines) + "\n")


def cmd_tabs(args: argparse.Namespace) -> int:
    from pagouse.observe import tabs

    data = tabs()
    payload = _envelope(ok=True, action="tabs", data=data)
    lines = [f"active={data.get('active')} tabs={len(data.get('tabs') or [])}"]
    for tab in data.get("tabs") or []:
        mark = ">" if tab.get("active") else " "
        lines.append(f"{mark} #{tab.get('id')} {tab.get('origin')}  {tab.get('title')}")
    return _print(payload, as_json=args.json, human="\n".join(lines) + "\n")


def cmd_snapshot(args: argparse.Namespace) -> int:
    from pagouse.observe import snapshot

    data = snapshot(
        args.tab,
        filter=args.filter,
        depth=args.depth,
        max_chars=args.max_chars,
    )
    payload = _envelope(ok=True, action="snapshot", data={"snapshot": data})
    return _print(payload, as_json=args.json, human=str(data.get("tree") or ""))


def cmd_wait(args: argparse.Namespace) -> int:
    from pagouse.observe import wait

    data = wait(
        args.tab,
        url_contains=args.url_contains,
        ref=args.ref,
        timeout_ms=args.timeout,
    )
    payload = _envelope(ok=True, action="wait", data=data)
    return _print(
        payload,
        as_json=args.json,
        human=f"matched {data.get('matched')} tab={data.get('tab_id')}\n",
    )


def cmd_shot(args: argparse.Namespace) -> int:
    from pagouse.observe import shot

    data = shot(args.tab, fit=args.fit)
    payload = _envelope(ok=True, action="shot", data={"shot": data})
    return _print(payload, as_json=args.json, human=str(data.get("path") or "") + "\n")


def cmd_scroll(args: argparse.Namespace) -> int:
    from pagouse.mutate import scroll

    data = scroll(
        args.ref,
        tab_id=args.tab,
        allow_input=args.allow_input,
        then=args.then,
        delay_ms=args.delay,
    )
    payload = _envelope(ok=True, action="scroll", data=data)
    return _print(payload, as_json=args.json, human=f"scrolled {args.ref}\n")


def cmd_click(args: argparse.Namespace) -> int:
    from pagouse.mutate import click

    data = click(
        args.ref,
        tab_id=args.tab,
        allow_input=args.allow_input,
        then=args.then,
        delay_ms=args.delay,
    )
    payload = _envelope(ok=True, action="click", data=data)
    return _print(payload, as_json=args.json, human=f"clicked {args.ref}\n")


def cmd_fill(args: argparse.Namespace) -> int:
    from pagouse.mutate import fill

    data = fill(
        args.ref,
        args.value,
        tab_id=args.tab,
        allow_input=args.allow_input,
        then=args.then,
        delay_ms=args.delay,
    )
    payload = _envelope(ok=True, action="fill", data=data)
    return _print(payload, as_json=args.json, human=f"filled {args.ref}\n")


def cmd_type(args: argparse.Namespace) -> int:
    from pagouse.mutate import type_text

    data = type_text(
        args.text,
        tab_id=args.tab,
        allow_input=args.allow_input,
        then=args.then,
        delay_ms=args.delay,
    )
    payload = _envelope(ok=True, action="type", data=data)
    return _print(payload, as_json=args.json, human=f"typed {data.get('typed')}\n")


def cmd_key(args: argparse.Namespace) -> int:
    from pagouse.mutate import key

    data = key(
        args.combo,
        tab_id=args.tab,
        allow_input=args.allow_input,
        then=args.then,
        delay_ms=args.delay,
    )
    payload = _envelope(ok=True, action="key", data=data)
    return _print(payload, as_json=args.json, human=f"key {args.combo}\n")


def cmd_navigate(args: argparse.Namespace) -> int:
    from pagouse.mutate import navigate

    data = navigate(
        args.url,
        tab_id=args.tab,
        allow_input=args.allow_input,
        then=args.then,
        delay_ms=args.delay,
    )
    payload = _envelope(ok=True, action="navigate", data=data)
    return _print(payload, as_json=args.json, human=f"navigate {data.get('url')}\n")


def cmd_tab_open(args: argparse.Namespace) -> int:
    from pagouse.mutate import tab_open

    data = tab_open(args.url, allow_input=args.allow_input, then=args.then, delay_ms=args.delay)
    payload = _envelope(ok=True, action="tab_open", data=data)
    return _print(payload, as_json=args.json, human=f"tab {data.get('tab_id')}\n")


def cmd_tab_focus(args: argparse.Namespace) -> int:
    from pagouse.mutate import tab_focus

    data = tab_focus(args.tab, allow_input=args.allow_input)
    payload = _envelope(ok=True, action="tab_focus", data=data)
    return _print(payload, as_json=args.json, human=f"focus {data.get('tab_id')}\n")


def cmd_daemon(args: argparse.Namespace) -> int:
    from pagouse.daemon import listen, stop

    if args.stop:
        stopped = stop()
        payload = _envelope(ok=True, action="daemon", data={"stopped": stopped, "daemon": False})
        return _print(payload, as_json=args.json, human="daemon stopped\n")
    return listen()


class _Parser(argparse.ArgumentParser):
    json_mode = False

    def error(self, message: str) -> Never:
        if _Parser.json_mode:
            payload = _envelope(ok=False, action="usage", error="usage", message=message)
            json.dump(payload, sys.stdout, indent=2)
            sys.stdout.write("\n")
            raise SystemExit(2)
        super().error(message)


def build_parser() -> argparse.ArgumentParser:
    p = _Parser(
        prog="pagouse",
        description="Observe (and with a grant, drive) a Chromium page.",
    )
    p.add_argument("--json", action="store_true", help="machine-readable envelope")
    p.add_argument("--verbose", action="store_true", help="enable debug logging")
    p.add_argument(
        "--allow-input",
        action="store_true",
        help="allow mutating commands (click/fill/type/key/navigate/tab_*)",
    )
    p.add_argument("--version", action="version", version=f"pagouse {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="extension, native host, and daemon readiness").set_defaults(
        func=cmd_doctor
    )
    sub.add_parser("tabs", help="list http(s) tabs").set_defaults(func=cmd_tabs)

    snap = sub.add_parser("snapshot", help="accessibility tree with ref_N labels")
    snap.add_argument("--tab", type=int, metavar="ID", help="tab id from tabs")
    snap.add_argument(
        "--filter",
        choices=("interactive", "all"),
        default="interactive",
        help="interactive controls only, or the full tree",
    )
    snap.add_argument("--depth", type=int, default=15)
    snap.add_argument("--max-chars", type=int, default=50000, dest="max_chars")
    snap.set_defaults(func=cmd_snapshot)

    shot = sub.add_parser("shot", help="capture the tab viewport")
    shot.add_argument("--tab", type=int, metavar="ID", help="tab id from tabs")
    shot.add_argument(
        "--fit",
        type=int,
        default=DEFAULT_FIT,
        metavar="PX",
        help=f"cap long edge in pixels (default {DEFAULT_FIT}; 0 disables)",
    )
    shot.set_defaults(func=cmd_shot)

    waiting = sub.add_parser("wait", help="poll until a URL substring or ref appears")
    waiting.add_argument("--tab", type=int, metavar="ID")
    waiting.add_argument("--url-contains", dest="url_contains", help="substring of the tab URL")
    waiting.add_argument("--ref", help="ref_N from snapshot")
    waiting.add_argument(
        "--timeout",
        type=int,
        default=5000,
        metavar="MS",
        help="milliseconds (default 5000)",
    )
    waiting.set_defaults(func=cmd_wait)

    then: dict[str, Any] = {
        "default": "none",
        "choices": ("none", "snapshot"),
        "help": "attach a fresh snapshot after the action",
    }

    sc = sub.add_parser("scroll", help="scroll a snapshot ref into view")
    sc.add_argument("--ref", required=True, help="ref_N from snapshot")
    sc.add_argument("--tab", type=int, metavar="ID")
    sc.add_argument("--then", **then)
    sc.add_argument(
        "--delay",
        type=int,
        default=450,
        metavar="MS",
        help="ms to wait before --then snapshot (default 450)",
    )
    sc.set_defaults(func=cmd_scroll)

    click = sub.add_parser("click", help="click the element for a snapshot ref")
    click.add_argument("--ref", required=True, help="ref_N from snapshot")
    click.add_argument("--tab", type=int, metavar="ID")
    click.add_argument("--then", **then)
    click.add_argument(
        "--delay",
        type=int,
        default=450,
        metavar="MS",
        help="ms to wait before --then snapshot (default 450)",
    )
    click.set_defaults(func=cmd_click)

    fill = sub.add_parser("fill", help="set a form control and fire input/change")
    fill.add_argument("--ref", required=True, help="ref_N from snapshot")
    fill.add_argument("--value", required=True)
    fill.add_argument("--tab", type=int, metavar="ID")
    fill.add_argument("--then", **then)
    fill.add_argument(
        "--delay",
        type=int,
        default=450,
        metavar="MS",
        help="ms to wait before --then snapshot (default 450)",
    )
    fill.set_defaults(func=cmd_fill)

    typ = sub.add_parser("type", help="type into the focused element of the tab")
    typ.add_argument("text")
    typ.add_argument("--tab", type=int, metavar="ID")
    typ.add_argument("--then", **then)
    typ.add_argument(
        "--delay",
        type=int,
        default=450,
        metavar="MS",
        help="ms to wait before --then snapshot (default 450)",
    )
    typ.set_defaults(func=cmd_type)

    key = sub.add_parser("key", help="press a combo such as Enter or ctrl+a")
    key.add_argument("combo")
    key.add_argument("--tab", type=int, metavar="ID")
    key.add_argument("--then", **then)
    key.add_argument(
        "--delay",
        type=int,
        default=450,
        metavar="MS",
        help="ms to wait before --then snapshot (default 450)",
    )
    key.set_defaults(func=cmd_key)

    nav = sub.add_parser("navigate", help="go to a URL, or back/forward")
    nav.add_argument("url")
    nav.add_argument("--tab", type=int, metavar="ID")
    nav.add_argument("--then", **then)
    nav.add_argument(
        "--delay",
        type=int,
        default=450,
        metavar="MS",
        help="ms to wait before --then snapshot (default 450)",
    )
    nav.set_defaults(func=cmd_navigate)

    opened = sub.add_parser("tab_open", help="open a new tab")
    opened.add_argument("url", nargs="?", default=None)
    opened.add_argument("--then", **then)
    opened.add_argument(
        "--delay",
        type=int,
        default=450,
        metavar="MS",
        help="ms to wait before --then snapshot (default 450)",
    )
    opened.set_defaults(func=cmd_tab_open)

    focus = sub.add_parser("tab_focus", help="activate a tab by id")
    focus.add_argument("--tab", type=int, required=True, metavar="ID")
    focus.set_defaults(func=cmd_tab_focus)

    daemon = sub.add_parser("daemon", help="run or stop the local router")
    daemon.add_argument("--stop", action="store_true", help="tear the daemon down")
    daemon.set_defaults(func=cmd_daemon)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    _Parser.json_mode = "--json" in argv
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    setup(verbose=args.verbose)
    try:
        return int(args.func(args))
    except PagouseError as exc:
        payload = _envelope(
            ok=False,
            action=getattr(args, "cmd", None) or "pagouse",
            error=exc.code,
            message=exc.message,
        )
        return _print(payload, as_json=bool(getattr(args, "json", False)), human=exc.message)


if __name__ == "__main__":
    raise SystemExit(main())
