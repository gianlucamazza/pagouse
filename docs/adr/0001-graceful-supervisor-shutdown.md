# ADR-0001: Give the browser supervisor ownership of graceful shutdown

Status: Accepted
Accepted by: Gianluca, 2026-09-28
Date: 2026-09-28

## Context

The installed isolated, headed and trusted services use `KillMode=control-group`.
Systemd sends SIGTERM to the supervisor and ChromeDriver together. The supervisor
then tries to delete the WebDriver session through a driver which may already be
exiting. Nine historical Chromium SIGABRTs coincide with stop requests. After the
independent startup-readiness fix, the isolated live probe reproduced a SIGABRT
on its first successful start/stop cycle, without leftover profile processes.
The observation supports this shutdown-order hypothesis; it is not yet a passing
validation of the proposed policy.

## Decision

Use `KillMode=mixed` and explicit `TimeoutStopSec=20s` in all three service units.
The initial SIGTERM goes only to the supervisor, which performs the existing
WebDriver session deletion and owned-process cleanup. Systemd retains bounded
SIGKILL escalation for processes remaining in the service cgroup after timeout.
Keep profile-based cleanup scoped to the exact owned profile; preserve the trusted
profile and ordinary Chromium sessions. Do not broaden process matching or hide
coredumps. Remove temporary profiles only after owned-process cleanup completes.

Validation: three successful isolated localhost start/stop cycles without a new
coredump or owned-process residue; unchanged ordinary browser/session state.
Also verify all three unit files have identical shutdown policy, exercise trusted
profile preservation hermetically, and run systemd unit verification. A failed
live retest falsifies the shutdown hypothesis and must remain in the record.

## Consequences

ChromeDriver remains available during graceful shutdown. Total stop latency is
bounded by 20 seconds, retaining forced cleanup for hung children. The desktop
may launch Chromium in a separate app scope; the existing exact-profile cleanup
remains necessary. Trusted shutdown is checked without opening real passkey or
1Password workflows. Only user-level unit files are installed; no `/etc` edits.

## Alternatives

- Keep `control-group`: reproduced abnormal exit; the protocol owner cannot
  guarantee driver availability during cleanup.
- Use `KillMode=process`: permits unbounded orphan children and drops group-level
  escalation.
- Suppress SIGABRT alerts: masks the fault without restoring orderly shutdown.
