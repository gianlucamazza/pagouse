# Changelog

## [0.4.0] — 2026-08-22

### Added

- `wait_ref` command: lightweight extension-side polling for a ref (no
  full AX walk). Available on CLI (`--json wait_ref`), MCP extra, and in
  the agent skill.
- `--verbose` flag and `PAGOUSE_LOG` environment variable for structured
  stdlib logging (levels: `debug`, `info`, `warning`, `error`).
- `--delay MS` on mutate commands (`click`, `fill`, `type`, `key`,
  `navigate`, `tab_open`, `scroll`) to configure the wait before
  `--then snapshot` (default 450 ms).
- `fit_skipped: true` in the `shot` envelope when ImageMagick is not
  installed, plus a stderr warning in non-JSON mode.
- `__all__` on core modules (`contract`, `errors`, `models`) to declare
  the public API.
- Explicit Content Security Policy in the extension manifest.
- Error code table in the agent skill (all 11 codes documented).
- Logging in `nm_relay.py`, `hosts/mcp.py`, and `daemon.py`.

### Changed

- `nm_relay.py` catches `json.JSONDecodeError` instead of bare
  `ValueError`, so `KeyboardInterrupt` and `SystemExit` are no longer
  swallowed.
- `pagoused` limits concurrent client threads to 16 via a semaphore.
- SPA pages: dead WeakRef entries are purged from `__pagouseRefs` on each
  new ref, preventing unbounded Map growth.

### Fixed

- Native-messaging retry limited to 5 attempts so Chromium can close
  cleanly when the daemon is unavailable.

### Removed

- Unused `storage` permission from the extension manifest.

## [0.3.0] — 2026-08-22

### Added

- Error code `restricted_page` (exit 1) for pages Chromium refuses to
  script, instead of a misleading `ipc_failed`.
- `tabs` rows carry `scriptable: false` for the Web Store gallery.
- `snapshot` may carry optional `frame_errors` when sub-frames cannot be
  read; the rest of the tree stays valid.
- `doctor` reports the connected extension's version and site access:
  a known mismatch blocks as `extension_version`; site access clears
  `shot_ready`.

### Fixed

- The native-messaging host template allowlists both extension ids
  (unpacked and Chrome Web Store), so a store install keeps working.
- `package-store.sh` verifies the store zip has no manifest `key`.

## [0.2.0] — 2026-08-22

### Added

- Brand icon set rendered from one SVG source in `extension/icons/src/`.
- Store packaging: `install/package-store.sh` builds a reproducible store
  zip from committed sources only.
- Publishing: `install/webstore-publish.py`, a stdlib-only Chrome Web Store
  uploader (upload, publish, status) driven by environment variables.
- Store listing copy, a typeset terminal screenshot, and a privacy policy.
- `install.sh` links the skill into `~/.config/opencode/skills` when that
  root already exists.

## [0.1.0] — 2026-08-22

### Added

- Chromium MV3 extension on the daily profile: accessibility snapshot with
  `ref_N` labels, viewport shot, tab list.
- Local daemon + native-messaging relay. No remote-debugging port, no Allow
  dialog, no `chrome.debugger`.
- CLI `--json` envelope `schema: 1`. Observe: `doctor`, `tabs`, `snapshot`,
  `shot`, `wait`. Mutate with `--allow-input`: `click`, `fill`, `type`,
  `key`, `navigate`, `scroll`, `tab_open`, `tab_focus`.
- Snapshots include iframe documents; refs are `ref_fFRAME_N`.
- Tabs the agent drives sit in a Chromium tab group titled **jarvis** (green).
- Observe-only MCP extra (`pagouse-mcp`).
- Origin policy: shipped scheme deny (`chrome:`, `file:`, …); user
  `allow_origins` / `deny_origins`. Password fields serialize as `[redacted]`.
- Agent skill. Not a seat adapter.
- `doctor` prefers the native-host path of a running Chromium and counts
  tabs when the extension is connected.

### Fixed

- Viewport `shot` requires Chromium `<all_urls>` (`captureVisibleTab` rejects
  `http://*/*` + `https://*/*`). Scheme deny in the core is unchanged.
