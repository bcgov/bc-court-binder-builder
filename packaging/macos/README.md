# macOS installer (.dmg)

`package.sh` builds **Court binder builder.app** and a drag-to-Applications disk image,
`dist/release/court-binder-builder-<version>-macos-<arch>.dmg` (about 37 MB). Everything the app needs is inside
the bundle (the app, the `managing-court-binders` scripts, the CSO links file, `pypdf`, the PdfCraft native engine
and Python), so people do not need Python.

The structure follows the PdfCraft packaging (`packaging/macos/` in https://github.com/richfrem/pdfcraft) and the
release process in [`docs/releasing.md`](../../docs/releasing.md): signing, notarization, a branded DMG window,
and a check that the app inside the image still passes `codesign --strict`. Installers are built by CI and
published as GitHub Release assets; the `.dmg` is never committed.

## Build it

On a Mac, from the repository root:

```bash
packaging/macos/package.sh
```

The script:
1. Creates its own build environment, `packaging/macos/.venv-build` (git-ignored), and installs
   `app/requirements-build.txt`. Nothing is installed into `app/.venv`.
2. **PdfCraft native engine.** Downloads the pinned pdfcraft wheel, checks its SHA-256 and installs it (without
   dependencies) into the build environment: what `pip install "<wheel url>"` does for a developer, done at build
   time so users never run `pip`.
3. Builds the app with PyInstaller (`binder_app.spec`).
4. **Signs it inside out** with the hardened runtime and `entitlements.plist` (ad hoc unless
   `MACOS_SIGN_IDENTITY` is set).
5. Runs the packaged app's **self-test**, `Court binder builder --selftest --require-pdfcraft`: a sample binder must
   pass all 20 gates and the bundled native engine must merge two PDFs. A broken bundle fails the build.
6. Builds the DMG (`hdiutil create -srcfolder`, with retries), signs it, mounts it and verifies the app inside with
   `codesign --verify --strict`.
7. With a real identity and Apple credentials, notarizes and staples the app and the DMG.

| Variable | Purpose |
| :--- | :--- |
| `MACOS_SIGN_IDENTITY`, `MACOS_KEYCHAIN` | Developer ID identity (CI sets them with `import-cert.sh`) |
| `APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID` | All three, with a real identity, enable notarization (untested here) |
| `PDFCRAFT_WHEEL_URL` / `PDFCRAFT_WHEEL_SHA256` | Wheel to download and its hash (defaults: v0.16.1, Python 3.13, Apple Silicon) |
| `PDFCRAFT_WHEEL` | Use a local wheel; the hash is checked only if `PDFCRAFT_WHEEL_SHA256` is also set |
| `WITH_PDFCRAFT=0` | Build without the native engine |
| `BUILD_PYTHON` | Python for the build environment (default `python3`; must match the wheel's tag, 3.13) |
| `CBB_VERSION`, `DIST` | Version override for a test run; output folder (default `dist/release`) |

## Install it

1. Open the `.dmg`.
2. Drag **Court binder builder** onto **Applications**.
3. Open it from Applications or Launchpad.

## Things to know

- **Architecture and Python:** the build matches the Mac it runs on. Built on Apple Silicon it gives an `arm64`
  image that does not run on Intel Macs, and the other way round. The published PdfCraft wheel is Python 3.13 on
  Apple Silicon only, so an Intel build needs an `x86_64` wheel (none is published) or `WITH_PDFCRAFT=0`.
- **The binder engine does not call PdfCraft yet.** The native engine is bundled and proven by the self-test, but
  the generator, assembler and validator still use their own code and `pypdf`.
- **Unsigned by default.** The app is ad-hoc signed, which is enough to run on the Mac that built it. A copy
  downloaded from the internet triggers Gatekeeper: right-click the app, choose **Open**, then **Open** again; or run
  `xattr -dr com.apple.quarantine "/Applications/Court binder builder.app"`. Signed, notarized builds need an Apple
  Developer ID (see `docs/releasing.md`); that path has not been exercised.
- **Folders:** an installed app saves to `~/Documents/BC Court Binder` (sample filings) and
  `~/Documents/BC Court Binder/Output` (binders) until you change them in the sidebar. Choices are stored in
  `~/.bc_court_binder_settings.json`, shared with a copy run from source on the same Mac.
- **No custom icon yet.** The app uses the default icon.

## Testing in isolation

macOS apps cannot run in a Linux container, so use one of these:

- **Sandbox on this Mac.** Mount the `.dmg` and run the self-test under `sandbox-exec` with a profile that blocks your
  repo, the system Python, Homebrew and the network, and a fresh `HOME`:
  ```bash
  cat > /tmp/profile.sb <<'EOP'
  (version 1)
  (allow default)
  (deny network*)
  (deny file-read* (subpath "/Users/YOU/Projects") (subpath "/Library/Frameworks/Python.framework") (subpath "/opt/homebrew") (subpath "/usr/local"))
  EOP
  hdiutil attach dist/release/*.dmg -nobrowse -readonly -mountpoint /tmp/mnt
  mkdir -p /tmp/h && env -i HOME=/tmp/h PATH=/usr/bin:/bin TMPDIR=/tmp/h \
    sandbox-exec -f /tmp/profile.sb "/tmp/mnt/Court binder builder.app/Contents/MacOS/Court binder builder" --selftest --require-pdfcraft
  hdiutil detach /tmp/mnt
  ```
  Expect `SELFTEST OK`. Run the project's own Python under the same profile first as a control; it must be blocked.
- **A new standard user account**, or a **virtual machine** (Tart or UTM), for a real clean-machine test including
  the Gatekeeper experience.

## Files

| File | Purpose |
| :--- | :--- |
| `package.sh` | Builds the app, signs it, self-tests it, makes and verifies the DMG, notarizes (optional) |
| `binder_app.spec` | PyInstaller specification: what goes in the bundle |
| `launcher.py` | Entry script that starts the app |
| `entitlements.plist` | Hardened-runtime entitlements (library validation off, as a PyInstaller bundle needs) |
| `import-cert.sh` | CI only: imports the Developer ID certificate into a temporary keychain |
| `dmg/` | The DMG window: background, Finder layout and the generator for both |
