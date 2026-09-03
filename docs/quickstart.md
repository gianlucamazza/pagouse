# Quickstart

Install the package with `./install.sh`. The installer does not touch an
existing Chromium profile or install an extension.

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
on `PATH`. The managed profile is temporary and is removed on stop.
