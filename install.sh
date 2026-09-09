#!/usr/bin/env bash
# Local install: uv tool + optional config + agent skill links.
# Idempotent. Does not register MCP and does not write host config.toml files.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${HOME}/.local/bin"
CFG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/pagouse"

need() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "pagouse: missing $1" >&2
		exit 1
	}
}

need uv
mkdir -p "$BIN" "$CFG_DIR"

uv tool install --force --reinstall "${REPO}[mcp]"

SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"
install -m 0644 "$REPO/install/pagouse-browser.service" "$SYSTEMD_USER_DIR/pagouse-browser.service"
install -m 0644 "$REPO/install/pagouse-browser-headed.service" "$SYSTEMD_USER_DIR/pagouse-browser-headed.service"
install -m 0644 "$REPO/install/pagouse-browser-trusted.service" "$SYSTEMD_USER_DIR/pagouse-browser-trusted.service"
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-system-running >/dev/null 2>&1; then
	systemctl --user daemon-reload
fi

if [[ ! -f "$CFG_DIR/config.toml" ]]; then
	umask 077
	cp "$REPO/examples/config.toml" "$CFG_DIR/config.toml"
	chmod 600 "$CFG_DIR/config.toml"
	echo "Created $CFG_DIR/config.toml"
fi

link_skill() {
	local dest="$1"
	mkdir -p "$dest"
	ln -sfn "$REPO/skills/pagouse/SKILL.md" "$dest/SKILL.md"
	echo "Linked skill → $dest/SKILL.md"
}

for root in \
	"${HOME}/.claude/skills" \
	"${HOME}/.grok/skills" \
	"${HOME}/.agents/skills"; do
	[[ -d "$root" ]] || continue
	link_skill "$root/pagouse"
done

echo
echo "pagouse --json doctor"
echo "Then run pagouse browser_start."
