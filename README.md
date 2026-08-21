# pagouse

[![CI](https://github.com/gianlucamazza/pagouse/actions/workflows/ci.yml/badge.svg)](https://github.com/gianlucamazza/pagouse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)

**Coding agents should not click web pages by pixel.** pagouse is a page
agent: a Chromium extension on the daily profile that returns an
accessibility tree with `ref_N` labels, and (with a grant) clicks, fills,
and navigates those nodes.

It observes by default. Mutation needs `--allow-input`. The optional MCP
server is observe-only and cannot be talked into typing.

```console
$ pagouse --json snapshot --tab 1840 | jq -r '.snapshot.tree' | head
RootWebArea "Inbox" [ref_1]
  textbox "Search" [ref_2]
  button "Compose" [ref_3]
```

## Requirements

- Python 3.13+
- A Chromium-family browser (Chrome, Chromium, Brave, Edge) on the **daily
  profile**
- The unpacked extension in `extension/` plus the native-messaging host

The Python core itself has **zero** dependencies. `magick` is optional for
`--fit` downscaling.

## Install

```bash
git clone https://github.com/gianlucamazza/pagouse
cd pagouse
./install.sh
```

Then load `extension/` unpacked (`chrome://extensions` → Developer mode).
`pagouse --json doctor` should report `ready` once the popup is green.

## License

MIT. See [LICENSE](LICENSE).
