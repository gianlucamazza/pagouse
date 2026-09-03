# Privacy policy

Effective date: 2026-08-22.

pagouse is a local page agent. This policy describes what happens to data
when you use the pagouse CLI and managed Chromium session.

## What pagouse collects

Nothing. pagouse has no servers, no accounts, no analytics, and no
telemetry. It makes no network calls other than to the pages you ask it to
drive.

## Where data goes

Page titles, URLs, accessibility trees, and viewport screenshots stay on
your machine:

- Snapshots, shots, and envelopes are printed to stdout or written under
  your runtime directory (`$XDG_RUNTIME_DIR/pagouse/`).
- WebDriver and CDP endpoints listen only on loopback during the owned
  Chromium session.
- Configuration lives in your user config directory.

Whatever leaves your machine leaves because *you* piped it there (for
example, giving CLI output to a coding agent). Treat page content as
untrusted input; see the security model for details.

## Permissions

The runtime starts Chromium with an isolated temporary profile and refuses
non-http(s) targets.

## Changes

Material changes to this policy ship with a release and are recorded in the
changelog.

## Contact

Gianluca Mazza — info@gianlucamazza.it
