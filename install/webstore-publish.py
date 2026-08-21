#!/usr/bin/env python3
"""Upload and publish the extension zip to the Chrome Web Store.

Stdlib only. Credentials come from the environment, never from this repo:

    PAGOUSE_CWS_CLIENT_ID      OAuth client id (Chrome Web Store API)
    PAGOUSE_CWS_CLIENT_SECRET  OAuth client secret
    PAGOUSE_CWS_REFRESH_TOKEN  long-lived refresh token for that client
    PAGOUSE_CWS_ITEM_ID        store item id (required unless --new)

Typical use after the first manual submission:

    python3 install/webstore-publish.py --upload dist/pagouse-extension-X.zip
    python3 install/webstore-publish.py --publish

The first item creation still happens in the dashboard (or via --new);
the listing fields themselves can only be edited there.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_BASE = "https://www.googleapis.com/upload/chromewebstore/v1.1/items"
ITEM_URL = "https://www.googleapis.com/chromewebstore/v1.1/items"


def _env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"webstore-publish: missing {name}", file=sys.stderr)
        raise SystemExit(2)
    return value


def _access_token() -> str:
    """Exchange the refresh token for a short-lived access token."""
    body = urllib.parse.urlencode(
        {
            "client_id": _env("PAGOUSE_CWS_CLIENT_ID"),
            "client_secret": _env("PAGOUSE_CWS_CLIENT_SECRET"),
            "refresh_token": _env("PAGOUSE_CWS_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return str(json.load(res)["access_token"])
    except urllib.error.HTTPError as exc:
        die_http(exc)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def die_http(exc: urllib.error.HTTPError) -> None:
    detail = exc.read().decode(errors="replace").strip()
    print(f"webstore-publish: HTTP {exc.code}: {detail}", file=sys.stderr)
    raise SystemExit(1)


def upload(zip_path: str) -> str:
    """Upload the zip. Returns the item id."""
    with open(zip_path, "rb") as fh:
        payload = fh.read()
    token = _access_token()
    if os.environ.get("PAGOUSE_CWS_ITEM_ID"):
        url = f"{UPLOAD_BASE}/{_env('PAGOUSE_CWS_ITEM_ID')}"
        req = urllib.request.Request(
            url, data=payload, method="PUT", headers=_headers(token),
        )
    else:
        req = urllib.request.Request(
            UPLOAD_BASE, data=payload, method="POST", headers=_headers(token),
        )
    req.add_header("Content-Type", "application/zip")
    try:
        with urllib.request.urlopen(req) as res:
            data = json.load(res)
    except urllib.error.HTTPError as exc:
        die_http(exc)
    item_id = str(data.get("id", ""))
    state = data.get("uploadState", "?")
    print(f"uploaded {zip_path} -> item {item_id or '(existing)'} [{state}]")
    return item_id


def publish(item_id: str, target: str) -> None:
    token = _access_token()
    query = urllib.parse.urlencode({"publishTarget": target})
    req = urllib.request.Request(
        f"{ITEM_URL}/{item_id}/publish?{query}", data=b"", method="POST",
        headers=_headers(token),
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.load(res)
    except urllib.error.HTTPError as exc:
        die_http(exc)
    status = data.get("status", [{}])[0]
    print(f"publish[{target}] {item_id}: {status.get('status', '?')} — "
          f"{status.get('statusDetail', '')}".rstrip(" —"))


def status(item_id: str) -> None:
    token = _access_token()
    projection = urllib.parse.urlencode({"projection": "DRAFT"})
    req = urllib.request.Request(
        f"{ITEM_URL}/{item_id}?{projection}", method="GET",
        headers=_headers(token),
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.load(res)
    except urllib.error.HTTPError as exc:
        die_http(exc)
    keep = {k: data[k] for k in ("id", "uploadState", "publicUrl") if k in data}
    print(json.dumps(keep, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--upload", metavar="ZIP", help="upload the store zip")
    parser.add_argument("--new", action="store_true",
                        help="create a new draft item instead of updating")
    parser.add_argument("--publish", action="store_true", help="publish to the public audience")
    parser.add_argument("--target", choices=("default", "trustedTesters"),
                        default="default", help="publish target")
    parser.add_argument("--status", action="store_true", help="print item status")
    args = parser.parse_args(argv)

    if not any((args.upload, args.publish, args.status)):
        parser.error("nothing to do: pass --upload, --publish, and/or --status")

    if args.upload:
        if args.new:
            # A fresh POST without an item id creates a new draft item.
            os.environ.pop("PAGOUSE_CWS_ITEM_ID", None)
        item_id = upload(args.upload)
    else:
        item_id = _env("PAGOUSE_CWS_ITEM_ID")

    if args.status:
        status(item_id)
    if args.publish:
        publish(item_id, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
