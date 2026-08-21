# Quickstart

```bash
git clone https://github.com/gianlucamazza/pagouse
cd pagouse
./install.sh
pagouse --json doctor
```

`install.sh` installs the uv tool, writes `~/.config/pagouse/config.toml` if
missing, links the skill into any existing agent skill root, and registers the
native-messaging host.

Then in Chromium: `chrome://extensions` → Developer mode → **Load unpacked** →
the **folder** `extension/` (not `manifest.json`). On the pagouse card, Site
access → **On all sites** (needed for `shot`). The popup is green when the
daemon is up. Tabs pagouse drives appear in the green **jarvis** tab group,
not Claude's.

```bash
pagouse --json tabs
pagouse --json snapshot --tab ID
pagouse --json --allow-input fill --ref ref_3 --value "user@example.com" --tab ID
pagouse --json --allow-input click --ref ref_4 --tab ID --then snapshot
```

This tool does not drive the compositor or native windows.
