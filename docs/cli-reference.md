# CLI reference

`pagouse --json <command>` is the agent surface. Without `--json` the same
commands print a short human summary. `--version` prints the package version.

Global flags: `--json`, `--verbose`, `--allow-input`, `--version`.

## Commands

| Command | Purpose |
|---------|---------|
| `browser_start` | Start Chromium via WebDriver BiDi; `--trusted` starts the persistent dedicated passkey profile |
| `browser_stop` | Stop the owned Chromium session |
| `browser_doctor` | Inspect the managed session |
| `contexts` | List managed browsing contexts |
| `doctor` | Managed WebDriver BiDi readiness. Branch on `ready`, not envelope `ok`. |
| `tabs` | Browsing contexts in managed Chromium |
| `snapshot` | Accessibility tree with `ref_N`. `--tab ID`, `--filter interactive\|all`, `--depth`, `--max-chars` |
| `passkey_status` | Detect a passkey/WebAuthn challenge and report external handoff availability. Optional `--tab ID` |
| `shot` | Viewport PNG. `--tab ID`, `--fit PX` (default 1568; `0` disables) |
| `wait` | Poll until `--url-contains` or `--ref`. `--tab ID`, `--timeout MS` (default 5000) |
| `wait_event` | Wait for a WebDriver BiDi event. `EVENT`, optional `--tab ID`, `--timeout MS` |
| `scroll` | `--ref ref_N` into view. Optional `--tab ID`, `--then snapshot`, `--delay MS` (default 450) |
| `click` | `--ref ref_N`. Optional `--tab ID`, `--then snapshot`, `--delay MS` (default 450) |
| `fill` | `--ref ref_N --value TEXT`. Optional `--tab ID`, `--then snapshot`, `--delay MS` (default 450) |
| `credential_fill` | `--credential HANDLE --field username\|password --ref ref_N`. Optional `--tab ID` |
| `type` | Unicode into the focused control. Optional `--tab ID`, `--then snapshot`, `--delay MS` (default 450) |
| `key` | Combo such as `Enter` or `ctrl+a`. Optional `--tab ID`, `--then snapshot`, `--delay MS` (default 450) |
| `navigate` | URL, or `back` / `forward`. Optional `--tab ID`, `--then snapshot`, `--delay MS` (default 450) |
| `tab_open` | Optional URL argument, `--then snapshot`, `--delay MS` (default 450) |
| `tab_focus` | `--tab ID` |

Mutate commands refuse with `readonly` (exit 2) without a grant — the flag,
an environment variable, or a config key. How the grant works:
[security-model.md](security-model.md).

## The MCP extra

The MCP extra exposes `doctor`, `tabs`, `snapshot`, `passkey_status`, `shot`, `wait`, and `wait_event`. All are
read-only. There is no mutate tool. Drive the page with the CLI and a grant.

Install: `uv tool install 'pagouse[mcp]'` then register `pagouse-mcp` with the
agent host. pagouse does not write the host's MCP config.

## Runtime

The installer provisions only the Python package and skill. Chromium is owned
by `browser_start` and released by `browser_stop`.
# Browser lifecycle

`pagouse browser_start` starts an isolated Chromium session through WebDriver
BiDi. Add `--headed` to show the browser window. `browser_stop` terminates the
owned session, `browser_doctor` reports its state, and `contexts` lists its
browsing contexts.
