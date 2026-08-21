# Architecture

## The problem

Coding agents click web pages by pixel and miss. pagouse is a page agent
*inside* Chromium: an accessibility tree with refs, fill, click, navigate,
on the daily profile.

It is not a compositor or seat adapter. Native windows and pixel clicks
are out of scope.

## Glossary

| Term | Meaning |
|------|---------|
| **ref** | Stable label (`ref_fFRAME_N`) for a node in the current document, including iframes. Stored as a `WeakRef` in that frame's isolated world. |
| **snapshot** | Indented accessibility tree with refs. Default filter is interactive controls. |
| **grant** | `--allow-input` / env / config. Observation never needs one. |
| **holder** | `pagoused`, a local daemon. The extension's native-messaging relay starts it. CLI never does. |
| **jarvis group** | Chromium tab group (`title: jarvis`, color green) for tabs pagouse is driving. Distinct from Claude in Chrome's group. |

## Layers

```
hosts/cli.py  hosts/mcp.py  skills/     # how you talk to pagouse
        │
   contract.py  (--json, schema 1)
        │
   core: models, errors, config, policy, safety, doctor,
         observe, mutate, session, shot, ax
        │
   daemon.py  (unix socket 0600)  nm_relay.py
        │
   extension MV3  (scripting, tabs, captureVisibleTab)
```

The extension does not speak to the agent. The daemon does not speak the
Chrome DevTools Protocol. Refs live in the page, so `snapshot` and `click`
can be separate CLI processes until the document goes away (`stale_ref`).

## Non-goals

- **An LLM inside the tool.** pagouse returns data; the agent decides.
- **chrome.debugger.** Exclusive per tab; would collide with Claude in Chrome
  and with DevTools. v0 uses `scripting` and `tabs` only.
- **Remote debugging / port 9222 / inspect Allow.** Out of scope.
- **Firefox / LibreWolf.** No equivalent of `chrome.scripting` + native
  messaging of this shape.
- **Arbitrary JavaScript in the page.** `javascript_tool` is not v0.
- **Pixel clicks.** Coordinates are out of scope.
- **A network daemon.** stdio + one owner-only unix socket.
- **MCP mutate.** The extra is observe-only.
