# Privacy policy

Effective date: 2026-08-22.

pagouse is a local page agent. This policy describes what happens to data
when you use the pagouse browser extension and CLI.

## What pagouse collects

Nothing. pagouse has no servers, no accounts, no analytics, and no
telemetry. It makes no network calls other than to the pages you ask it to
drive.

## Where data goes

Page titles, URLs, accessibility trees, and viewport screenshots stay on
your machine:

- Snapshots, shots, and envelopes are printed to stdout or written under
  your runtime directory (`$XDG_RUNTIME_DIR/pagouse/`).
- The daemon listens only on a local unix socket with owner-only
  permissions.
- Configuration lives in your user config directory.

Whatever leaves your machine leaves because *you* piped it there (for
example, giving CLI output to a coding agent). Treat page content as
untrusted input; see the security model for details.

## Permissions

The extension requests browser permissions solely to implement the agent
surface described in the documentation: reading tab state, injecting the
content script that builds accessibility snapshots, grouping driven tabs,
and talking to the local daemon over native messaging. Non-http(s) targets
are always refused.

## Changes

Material changes to this policy ship with a release and are recorded in the
changelog.

## Contact

Gianluca Mazza — info@gianlucamazza.it
