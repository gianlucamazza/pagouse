# Changelog

## [Unreleased]

### Added

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
