# Documentation

[← back to the project README](../README.md)

## Start here

| Page | For |
|------|-----|
| [quickstart.md](quickstart.md) | Install, load the extension, first snapshot |

## Reference

| Page | For |
|------|-----|
| [cli-reference.md](cli-reference.md) | Every command and flag, and the MCP surface |
| [json-contract.md](json-contract.md) | The `--json` envelope, per-action keys, error codes. **Authoritative** |
| [configuration.md](configuration.md) | `config.toml` keys and every environment variable |

## Understanding

| Page | For |
|------|-----|
| [architecture.md](architecture.md) | What problem this solves, the layers, the non-goals |
| [security-model.md](security-model.md) | The page grant, scheme deny, untrusted data |
| [release.md](release.md) | Cut a release and ship it to the Chrome Web Store |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Dev loop, test suite, layout rules |

## Conventions

Facts live in exactly one place and are linked from the others.
`tests/test_docs_alignment.py` checks flags, error codes, MCP tools, `doctor`
keys, environment variables, and every relative link on this page.
