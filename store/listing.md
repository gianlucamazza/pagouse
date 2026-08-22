# Chrome Web Store listing

Copy-and-paste source of truth for the store listing form. Keep facts in sync
with docs/json-contract.md and docs/security-model.md.

## Item metadata

- **Name:** pagouse
- **Short description** (≤132 chars):
  Page agent for coding agents: read pages by accessibility, act by ref —
  never by pixel. Local daemon, observe by default.
- **Category:** Developer Tools
- **Language:** English
- **Single purpose:** A page agent that lets coding agents observe a Chromium
  page through its accessibility tree and, with an explicit grant, act on it
  by reference instead of pixels.

## Screenshots

- `screenshots/1280x800.png` — terminal session (1280×800).

## Detailed description

By ref, not by pixel. pagouse is a page agent for coding agents: it reads
Chromium pages through their accessibility tree, hands your agent stable ref
labels, and — only with an explicit grant — clicks, fills, types, and
navigates those nodes.

- Observe by default. Mutation requires an explicit grant (--allow-input).
- Refs live inside the page, so snapshots and actions can run as separate
  CLI invocations.
- Local daemon over native messaging. No remote-debugging port, no
  chrome.debugger, no cloud service: page data never leaves your machine
  except through the agent you ran yourself.
- Optional MCP extra is observe-only; there is no mutate tool on it.
- Password fields are redacted in snapshots.
- Ships a scheme denylist (chrome:, file:, data:, javascript:, ...) and user
  origin allow/deny policies.

## Permission justifications

| Permission | Why |
|------------|-----|
| nativeMessaging | Required to start and talk to the local pagouse daemon that routes commands to the extension. |
| tabs | Read tab id, URL, title, and active state to answer the tabs command; open and focus tabs on request. |
| tabGroups | Put tabs the agent drives into a dedicated tab group so they stay visually separated. |
| scripting | Inject the content script that builds the accessibility snapshot with refs and performs clicks, fills, typing, and scrolling by ref. |
| storage | Remember small popup UI state only. |
| Host permission `<all_urls>` | The agent can be pointed at any http(s) site the user chooses, and captureVisibleTab rejects two-pattern match patterns, so a full origin list is required at install time. Non-http(s) targets are refused in code regardless. |

## Compliance notes

- No remote hosted code; everything ships in this package.
- No data collection: no analytics, no telemetry, no network calls to third
  parties. See the privacy policy:
  <https://github.com/gianlucamazza/pagouse/blob/main/docs/privacy-policy.md>
- Security policy: <https://github.com/gianlucamazza/pagouse/blob/main/SECURITY.md>
