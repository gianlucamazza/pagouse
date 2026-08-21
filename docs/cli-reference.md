# CLI reference

`pagouse --json <command>` is the agent surface. Without `--json` the same
commands print a short human summary. `--version` prints the package version.

Global flags: `--json`, `--allow-input`, `--version`.

## Commands

| Command | Purpose |
|---------|---------|
| `doctor` | Native host, daemon, extension. Branch on `ready`, not envelope `ok`. |
| `tabs` | http(s) tabs in the daily profile |
| `snapshot` | Accessibility tree with `ref_N`. `--tab ID`, `--filter interactive\|all`, `--depth`, `--max-chars` |
| `shot` | Viewport PNG. `--tab ID`, `--fit PX` (default 1568; `0` disables) |
| `wait` | Poll until `--url-contains` or `--ref`. `--tab ID`, `--timeout MS` (default 5000) |
| `scroll` | `--ref ref_N` into view. Optional `--tab ID`, `--then snapshot` |
| `click` | `--ref ref_N`. Optional `--tab ID`, `--then snapshot` |
| `fill` | `--ref ref_N --value TEXT`. Optional `--tab ID`, `--then snapshot` |
| `type` | Unicode into the focused control. Optional `--tab ID`, `--then snapshot` |
| `key` | Combo such as `Enter` or `ctrl+a`. Optional `--tab ID`, `--then snapshot` |
| `navigate` | URL, or `back` / `forward`. Optional `--tab ID`, `--then snapshot` |
| `tab_open` | Optional URL argument, `--then snapshot` |
| `tab_focus` | `--tab ID` |
| `daemon` | Foreground router. `--stop` tears it down |

Mutate commands refuse with `readonly` (exit 2) without a grant — the flag,
an environment variable, or a config key. How the grant works:
[security-model.md](security-model.md).

## The MCP extra

The MCP extra exposes `doctor`, `tabs`, `snapshot`, `shot`, and `wait`. All are
read-only. There is no mutate tool. Drive the page with the CLI and a grant.

Install: `uv tool install 'pagouse[mcp]'` then register `pagouse-mcp` with the
agent host. pagouse does not write the host's MCP config.

## Native host

`install/install-host.sh` writes `it.gianlucamazza.pagouse.json` into each
Chromium-family `NativeMessagingHosts` directory that already exists, and a
wrapper at `~/.local/bin/pagouse-nm-host`. The extension's native port keeps
one daemon (`pagoused`) for the session. Load `extension/` unpacked.
