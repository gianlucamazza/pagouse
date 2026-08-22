# Release

How to cut a pagouse release and ship it to the Chrome Web Store.

## Extension ids: local and store are different

The manifest carries a `key` so a local **unpacked** load pins the id
`omnnhbbobflobnhmlfibhobmeodacbig`. The store rejects that field in
uploaded packages, so it assigns its own id — currently
`nahhkjknnnnmehcppbiimcobbicigfac` (read it from the dashboard item URL
after the first upload). `install/package-store.sh` strips `key` from the
store zip and verifies it stayed stripped. The native-messaging host
template allowlists both ids; if the store ever re-assigns one, add it
there.

## Version bump

Three places, always together:

1. `src/pagouse/__init__.py` — `__version__`
2. `extension/manifest.json` — `"version"`
3. `CHANGELOG.md` — a new `## [X.Y.Z]` section (the test suite enforces it)

Then:

```bash
uv run pytest
uv run ruff check src tests && uv run ruff format --check src tests
uv run ty check src
```

## Package and publish to GitHub

```bash
install/package-store.sh          # dist/pagouse-extension-X.Y.Z.zip from committed sources
git add -A && git commit -m "chore: release X.Y.Z"
git tag vX.Y.Z && git push --tags
gh release create vX.Y.Z dist/pagouse-extension-*.zip --title "vX.Y.Z" --notes "…"
```

`package-store.sh` refuses to build if `extension/` is dirty or the two
version stamps disagree.

## Chrome Web Store

### One-time setup

1. Register on the [Chrome Web Store dashboard](https://chrome.google.com/webstore/devconsole)
   (one-time fee). Note the **item id** after creating it.
2. In Google Cloud Console create an OAuth client for the Chrome Web Store
   API, then mint a refresh token with the OAuth Playground using scope
   `https://www.googleapis.com/auth/chromewebstore`.
3. Export the secrets — never commit them:

```bash
export PAGOUSE_CWS_CLIENT_ID=...
export PAGOUSE_CWS_CLIENT_SECRET=...
export PAGOUSE_CWS_REFRESH_TOKEN=...
export PAGOUSE_CWS_ITEM_ID=...
```

4. Create the listing in the dashboard following `store/listing.md`
   (description, single purpose, permission justifications, screenshot at
   `store/screenshots/1280x800.png`, privacy policy URL:
   <https://github.com/gianlucamazza/pagouse/blob/main/docs/privacy-policy.md>).
5. Upload the zip (dashboard or step below) and submit for review.

### Subsequent releases

```bash
python3 install/webstore-publish.py --upload dist/pagouse-extension-X.Y.Z.zip
python3 install/webstore-publish.py --publish            # public audience
python3 install/webstore-publish.py --status             # review state
```

`--target trustedTesters` publishes to testers instead. The `<all_urls>`
host permission means every update goes through human review; plan for a
waiting period before tagging the release as shipped.

## After publishing

On an installed machine: `pagouse --json doctor` should still report
`ready`. The host manifest allowlists both the unpacked and the store
extension ids; installs made before a store build existed need one
re-run of `install/install-host.sh` to pick up both entries.
