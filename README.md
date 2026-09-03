# pagouse

[![CI](https://github.com/gianlucamazza/pagouse/actions/workflows/ci.yml/badge.svg)](https://github.com/gianlucamazza/pagouse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)

**By ref, not by pixel.** pagouse is a page agent for coding agents: a
Chromium page agent that owns an isolated browser session, reads the
browser-computed accessibility tree, and — only with a grant — interacts with
the page through WebDriver BiDi.

It observes by default. Mutation needs `--allow-input`. The optional MCP
server is observe-only and cannot be talked into typing.

```console
$ pagouse --json snapshot --tab 1840 | jq -r '.snapshot.tree' | head
RootWebArea "Inbox" [ref_1]
  textbox "Search" [ref_2]
  button "Compose" [ref_3]
```

## How it works

- `browser_start` starts Chromium with a temporary, owner-only profile and
  persists only local session metadata.
- WebDriver BiDi handles lifecycle, navigation, contexts and trusted input;
  CDP is restricted to the browser-computed accessibility tree.
- A versioned `--json` envelope (`schema: 2`) is shared by CLI and MCP.

The layers and the non-goals: [docs/architecture.md](docs/architecture.md).

## Requirements

- Linux
- Python 3.13+ and [`uv`](https://docs.astral.sh/uv/)
- Chromium and a matching ChromeDriver on the host

The core itself has **zero** dependencies. `magick` is optional for `--fit`
downscaling.

## Install

```bash
git clone https://github.com/gianlucamazza/pagouse
cd pagouse
./install.sh
```

`install.sh` installs pagouse as a `uv` tool, writes the optional config if
missing, and links the agent skill. Then run `pagouse browser_start`.

## Usage

Observe — never needs a grant:

```bash
pagouse --json tabs
pagouse --json snapshot --tab ID
```

Drive — add `--allow-input`, click by `ref`, never by coordinates:

```bash
pagouse --json --allow-input click --ref ref_4 --tab ID --then snapshot
```

Every command and flag: [docs/cli-reference.md](docs/cli-reference.md). The
envelope and error codes: [docs/json-contract.md](docs/json-contract.md).

## MCP extra and agent skill

`uv tool install 'pagouse[mcp]'` provides `pagouse-mcp`: read-only observation
tools only. There is no mutate tool; drive the page through the CLI and a grant.

`install.sh` also links `skills/pagouse/SKILL.md` into any existing agent
skill root, so your agents get the playbook without setup.

## Security

Observation never asks permission; mutation refuses without an explicit
grant. Scheme deny, origin policy, and secret redaction are enforced in the
core. Tab titles, URLs, tree text, and shot pixels are **untrusted input**.
Read [docs/security-model.md](docs/security-model.md) before enabling
input. Report vulnerabilities per [SECURITY.md](SECURITY.md).

## Documentation

| Page | For |
|------|-----|
| [docs/quickstart.md](docs/quickstart.md) | Install, start the managed browser, first commands |
| [docs/cli-reference.md](docs/cli-reference.md) | Every command and flag, and the MCP surface |
| [docs/json-contract.md](docs/json-contract.md) | The `--json` envelope, per-action keys, error codes. **Authoritative** |
| [docs/configuration.md](docs/configuration.md) | `config.toml` keys and every environment variable |
| [docs/architecture.md](docs/architecture.md) | What problem this solves, the layers, the non-goals |
| [docs/security-model.md](docs/security-model.md) | The page grant, scheme deny, untrusted data |

## License

MIT. See [LICENSE](LICENSE).
