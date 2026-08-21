#!/usr/bin/env bash
# Register the pagouse native-messaging host for Chromium-family browsers.
# Idempotent, no sudo.
set -euo pipefail

HOST_NAME="it.gianlucamazza.pagouse"
REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
TEMPLATE="$REPO_DIR/install/$HOST_NAME.json.in"

need() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "pagouse: missing $1" >&2
		exit 1
	}
}

need uv

# Prefer the uv-tool install so Chromium does not depend on this checkout.
BIN="${PAGOUSE_NM_BIN:-}"
if [[ -z "$BIN" ]]; then
	if command -v pagouse-nm >/dev/null 2>&1; then
		BIN="$(command -v pagouse-nm)"
	else
		uv tool install --force --reinstall "${REPO_DIR}[mcp]" >/dev/null
		BIN="$(command -v pagouse-nm)"
	fi
fi
[[ -x "$BIN" ]] || {
	echo "pagouse-nm not executable: $BIN" >&2
	exit 1
}

mkdir -p "$HOME/.local/bin"
WRAPPER="$HOME/.local/bin/pagouse-nm-host"
wrapper_src="$(cat "$REPO_DIR/install/pagouse-nm.sh.in")"
printf '%s\n' "${wrapper_src//@BIN@/$BIN}" >"$WRAPPER"
chmod +x "$WRAPPER"
echo "wrapper: $WRAPPER -> $BIN"

template="$(cat "$TEMPLATE")"
manifest="${template//@PATH@/$WRAPPER}"
XDG="${XDG_CONFIG_HOME:-$HOME/.config}"
dirs=(
	"$XDG/google-chrome/NativeMessagingHosts"
	"$XDG/google-chrome-beta/NativeMessagingHosts"
	"$XDG/chromium/NativeMessagingHosts"
	"$XDG/BraveSoftware/Brave-Browser/NativeMessagingHosts"
	"$XDG/microsoft-edge/NativeMessagingHosts"
	"$XDG/vivaldi/NativeMessagingHosts"
)
for dir in "${dirs[@]}"; do
	parent="$(dirname "$dir")"
	[[ -d "$parent" ]] || continue
	mkdir -p "$dir"
	printf '%s\n' "$manifest" >"$dir/$HOST_NAME.json"
	echo "installed: $dir/$HOST_NAME.json"
done

echo
echo "Load the unpacked extension in Chromium:"
echo "  chrome://extensions -> Developer mode -> Load unpacked"
echo "  $REPO_DIR/extension"
echo "The daemon is auto-started by the native-messaging relay."
