# Security policy

pagouse reads the pages in your daily Chromium profile and, with an explicit
grant, clicks, fills, and navigates as you. A bug here is not a crash — it is
mail sent from your account. Reports are welcome.

## Reporting a vulnerability

Email **info@gianlucamazza.it** with `pagouse` in the subject. Please do not
open a public issue for a vulnerability.

Include what you need to make it reproducible: the version
(`pagouse --version`), the browser and its version, and the smallest set of
steps that shows the problem.

This is a single-maintainer project, so treat these as intent rather than a
contractual SLA: acknowledgement within a week, an assessment within two, and
coordinated disclosure once a fix ships.

## Supported versions

Only the latest release gets fixes. There are no maintenance branches.

## Threat model

**Trusted.** The local user and the Chromium profile they attached.

**Untrusted.** Everything that reaches it from a page: titles, URLs,
accessibility trees, shot pixels. An agent that follows instructions found
there has been prompt-injected.

**Out of scope.** That an input-enabled session can click anywhere on an
allowed origin — that is the feature, gated behind `--allow-input`.
