# Architecture

pagouse is a page agent for Chromium. It owns a dedicated Chromium process and
uses WebDriver BiDi for lifecycle, contexts, navigation and input. CDP is an
explicitly narrow adapter used only for the browser-computed accessibility
tree, because that capability is not yet standardised by WebDriver BiDi.

It is not a compositor or seat adapter. Native windows and desktop pixels are
out of scope.

## Layers

```
hosts/cli.py  hosts/mcp.py  skills/
        |
contract.py  (schema 2)
        |
BrowserSession / BiDiClient / browserd
        |                    \
WebDriver BiDi              CDP AX adapter
        |
owned Chromium + isolated user-data-dir
```

Passkey authentication is an explicit human-approved handoff to a separate
trusted local browser profile. The isolated pagouse profile does not receive
the 1Password extension or WebAuthn private keys. Trusted mode is headed,
persistent, dedicated to pagouse, and must never reuse the daily Chromium
profile.

The persistent `pagouse-browserd` owner is launched on demand by a
`systemd --user` unit. Session metadata is atomic and owner-readable so
separate CLI invocations can reconnect to the same managed browser. The browser
profile is temporary and is deleted on `browser_stop`.
`pagouse-browser-trusted.service` is a separate headed unit using the
owner-only persistent profile under the XDG data directory. Headed managed
browser windows use the dedicated `pagouse-browser` desktop identity so launchers
do not mistake them for the user's daily Chromium session.

## Safety boundaries

- MCP exposes observation only; mutation stays in the CLI and requires the
  explicit input grant.
- CDP is not a general-purpose escape hatch: only `Accessibility.getFullAXTree`
  and the minimum DOM geometry lookup used to target a ref are allowed.
- Ref tokens are capability handles tied to the managed session and current
  document. A new snapshot is required after navigation or a stale ref.
- No remote debugger is bound to a non-loopback address.

## Non-goals

- An LLM inside the tool.
- Desktop, compositor, seat or native-window automation.
- Arbitrary JavaScript supplied by the agent.
- A network service or MCP mutation tool.
