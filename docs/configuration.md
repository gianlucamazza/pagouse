# Configuration

Copy [examples/config.toml](../examples/config.toml) to
`~/.config/pagouse/config.toml` (or `$XDG_CONFIG_HOME/pagouse/config.toml`).
Missing file = defaults. Override the path with `PAGOUSE_CONFIG`.

```toml
allow_input = false

[policy]
allow_origins = []
deny_origins = []
```

Optional credential handles use the template in
[`examples/credentials.toml`](../examples/credentials.toml), copied to a
separate owner-only file at
`~/.config/pagouse/credentials.toml`. It contains only 1Password secret
references, never resolved values:

```toml
[credentials.example_login]
origin = "https://example.com"
username = "op://Pagouse/Example Login/username"
password = "op://Pagouse/Example Login/password"
```

`credential_fill` accepts only configured handles and `username`/`password`.
It resolves values through `op read` only for the duration of the action.

| Key | Default | Meaning |
|-----|---------|---------|
| `allow_input` | `false` | Page grant for click/fill/type/key/navigate/tab_* |
| `policy.allow_origins` | `[]` | Empty: all http(s) once granted. Non-empty: only these origins |
| `policy.deny_origins` | `[]` | Origins that always raise `denied` |

A bare string in a list key is one token, not a sequence of characters.

## Environment

| Variable | Meaning |
|----------|---------|
| `PAGOUSE_CONFIG` | Absolute path to `config.toml` (wins over XDG) |
| `PAGOUSE_ALLOW_INPUT` | `1` / `true` / `yes` — page grant for this process |
| `PAGOUSE_LOG` | Log level: `debug`, `info`, `warning` (default), `error` |
| `PAGOUSE_CHROMIUM` | Optional absolute path to the Chromium binary |
| `PAGOUSE_CHROMEDRIVER` | Optional absolute path to the matching ChromeDriver binary |
| `XDG_CONFIG_HOME` | Config root; also searched for Chromium NativeMessagingHosts |
| `XDG_RUNTIME_DIR` | Session metadata, lock, and shot files (`$XDG_RUNTIME_DIR/pagouse/`) |

Non-http(s) schemes (`chrome:`, `file:`, …) are always denied by the shipped
list in [security-model.md](security-model.md). Origin tokens are yours to
name; pagouse ships no denylist of sites.
