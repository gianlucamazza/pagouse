# Changelog

## [0.1.0] — 2026-08-21

### Added

- `wait` (URL substring or ref, with timeout) and `scroll --ref`. Snapshots
  include iframe documents; refs are `ref_fFRAME_N`.
- Tabs pagouse drives are moved into a Chromium tab group titled **jarvis**
  (green), so they do not sit in Claude in Chrome's group.
- `doctor` prefers the native-host path of a running Chromium, and counts
  tabs when the extension is connected. `--then snapshot` waits briefly so
  a click-driven navigation is visible.

### Changed

- User-facing playbook (skill, JSON contract, quickstart) documents only
  pagouse. It does not teach a seat CLI.

### Fixed

- **Viewport `shot` required `<all_urls>`.** Chromium's `captureVisibleTab`
  rejects `http://*/*` + `https://*/*` with an uncaught promise. Host
  permission is now `<all_urls>`; scheme deny in the core is unchanged.

### Added

- Chromium MV3 extension on the daily profile: accessibility snapshot with
  `ref_N` labels, viewport shot, tab list.
- Local daemon + native-messaging relay. No remote-debugging port, no Allow
  dialog, no `chrome.debugger` (so it can sit next to Claude in Chrome).
- CLI `--json` envelope `schema: 1`. Observe: `doctor`, `tabs`, `snapshot`,
  `shot`. Mutate with `--allow-input`: `click`, `fill`, `type`, `key`,
  `navigate`, `tab_open`, `tab_focus`.
- Observe-only MCP extra (`pagouse-mcp`).
- Origin policy: shipped scheme deny (`chrome:`, `file:`, …); user
  `allow_origins` / `deny_origins`. Password fields serialize as `[redacted]`.
- Agent skill. Not a seat adapter.
