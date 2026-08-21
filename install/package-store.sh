#!/usr/bin/env bash
# Build the Chrome Web Store zip from committed extension/ sources.
# Fails if extension/ is dirty or the two version stamps disagree.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

die() {
	echo "package-store: $*" >&2
	exit 1
}

command -v git >/dev/null 2>&1 || die "git not found"
command -v python3 >/dev/null 2>&1 || die "python3 not found"

MANIFEST_VER="$(python3 -c 'import json; print(json.load(open("extension/manifest.json"))["version"])')"
CORE_VER="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' src/pagouse/__init__.py)"
[[ -n "$MANIFEST_VER" ]] || die "cannot read version from extension/manifest.json"
[[ "$MANIFEST_VER" == "$CORE_VER" ]] ||
	die "version mismatch: manifest $MANIFEST_VER vs core $CORE_VER"

[[ -z "$(git status --porcelain -- extension)" ]] ||
	die "extension/ has uncommitted changes; commit them first"

mkdir -p dist
OUT="dist/pagouse-extension-$MANIFEST_VER.zip"
git archive --format=zip -o "$OUT" HEAD:extension

echo "$OUT"
