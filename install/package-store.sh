#!/usr/bin/env bash
# Build the Chrome Web Store zip from committed extension/ sources.
# Fails if extension/ is dirty or the two version stamps disagree.
#
# The store rejects a "key" field in manifest.json, but local unpacked
# loads rely on it to pin the extension id for the native-messaging
# allowlist. So: stage HEAD:extension, drop "key", zip the staging copy.
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

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
OUT="dist/pagouse-extension-$MANIFEST_VER.zip"
git archive --format=tar HEAD:extension | tar -x -C "$STAGE"

python3 - "$STAGE" "$OUT" <<'EOF'
import json, os, sys, zipfile

stage, out = sys.argv[1], sys.argv[2]
manifest = os.path.join(stage, "manifest.json")
with open(manifest) as fh:
    data = json.load(fh)
if data.pop("key", None) is not None:
    print("package-store: dropped manifest key for the store build")
with open(manifest, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")

entries = []
for root, _dirs, files in os.walk(stage):
    for name in files:
        full = os.path.join(root, name)
        entries.append((os.path.relpath(full, stage), full))
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for rel, full in sorted(entries):
        zf.write(full, rel)

# The store rejects the key field; verify the artifact we just wrote.
with zipfile.ZipFile(out) as zf:
    if b'"key"' in zf.read("manifest.json"):
        print("package-store: manifest key survived packaging", file=sys.stderr)
        raise SystemExit(1)
print(f"package-store: {out}")
EOF
