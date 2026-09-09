# Quickstart

Install the package with `./install.sh`. The installer does not touch an
existing Chromium profile or install an extension. Use `browser_start --trusted`
only with the dedicated local 1Password profile configured for passkeys.

Start an isolated browser:

```bash
pagouse --json browser_start
pagouse --json browser_doctor
pagouse --json contexts
```

Use the returned context id with `tabs`, `snapshot`, `navigate`, and the input
commands. Observation is read-only; mutation requires `--allow-input`.

Stop the owned browser when finished:

```bash
pagouse --json browser_stop
```

Set `PAGOUSE_CHROMIUM` or `PAGOUSE_CHROMEDRIVER` when binaries are not found
on `PATH`. The default managed profile is temporary and is removed on stop;
the trusted profile is persistent and never reuses the daily browser profile.
