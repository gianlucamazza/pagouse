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
BrowserSession / BiDiClient
        |                    \
WebDriver BiDi              CDP AX adapter
        |
owned Chromium + isolated user-data-dir
```

The session is persisted only as local owner-readable metadata so separate CLI
invocations can use the same managed browser. The browser profile is temporary
and is deleted on `browser_stop`.

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
