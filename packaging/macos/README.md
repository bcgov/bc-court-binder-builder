# macOS installer (.dmg)

Builds **Court binder builder.app** and a drag-to-Applications disk image. Everything the app needs is inside the bundle (the app, the `managing-court-binders` scripts, the CSO links file, `pypdf`, the PdfCraft native engine and Python), so people do not need Python.

## Build it

From the repository root, on a Mac:

```bash
packaging/macos/build_dmg.sh
```

The script:
1. Creates its own build environment, `packaging/macos/.venv-build` (git-ignored), and installs `app/requirements-build.txt` into it. Nothing is installed into `app/.venv`.
2. **PdfCraft native engine.** Downloads the pdfcraft wheel, checks its SHA-256 against the pinned value and installs it (without dependencies) into the build environment. This is what `pip install "<wheel url>"` does for a developer, done once at build time so users never run `pip`.
3. Builds **Court binder builder.app** with PyInstaller, signs it (ad-hoc unless `SIGN_IDENTITY` is set), and writes the `.dmg` (about 40 MB).
4. Runs the packaged app's **self-test**, `Court binder builder --selftest --require-pdfcraft`: it builds a sample binder and requires all 20 gates, loads the CSO links, and merges two PDFs with the bundled native engine. A broken bundle fails the build.

| Variable | Purpose |
| :--- | :--- |
| `PDFCRAFT_WHEEL_URL` / `PDFCRAFT_WHEEL_SHA256` | Wheel to download and its expected hash (defaults: v0.16.1, Python 3.13, Apple Silicon, `53f52d2f154d723c…`). Update both together. |
| `PDFCRAFT_WHEEL` | Use a local wheel (for example one built in `../pdfcraft`); the hash is checked only if `PDFCRAFT_WHEEL_SHA256` is also set |
| `WITH_PDFCRAFT=0` | Build without the native engine |
| `BUILD_PYTHON` | Python used to create the build environment (default `python3`; must match the wheel's tag, 3.13) |
| `SIGN_IDENTITY`, `NOTARY_PROFILE` | Developer ID signing and notarization (untested here) |

Output: `packaging/macos/dist/Court-binder-builder-<version>-macos-<arch>.dmg`. `build/`, `dist/` and `.venv-build/` are git-ignored; do not commit the `.dmg`. Publish it as a GitHub Release asset.

## Install it

1. Open the `.dmg`.
2. Drag **Court binder builder** onto **Applications**.
3. Open it from Applications or Launchpad.

## Things to know

- **Architecture and Python:** the build matches the Mac it runs on. Built on Apple Silicon it gives an `arm64` image that does not run on Intel Macs, and the other way round. The published PdfCraft wheel is Python 3.13 on Apple Silicon only, so an Intel build needs an `x86_64` wheel (none is published) or `WITH_PDFCRAFT=0`.
- **The binder engine does not call PdfCraft yet.** The native engine is bundled and proven to work by the self-test, but the generator, assembler and validator still write and read PDFs with their own code and `pypdf`. It is there for when the engine starts using it (for example merging original PDFs as true copies).
- **Unsigned by default.** The app is ad-hoc signed, which is enough to run on the Mac that built it. When a copy is downloaded from the internet, macOS Gatekeeper says the developer cannot be verified. Users can right-click the app, choose **Open**, then **Open** again; or run `xattr -dr com.apple.quarantine "/Applications/Court binder builder.app"`.
- **Signed and notarized builds** need an Apple Developer ID. The script supports them but this path has not been tested here:
  ```bash
  SIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
  NOTARY_PROFILE="my-notary-profile" \
  packaging/macos/build_dmg.sh
  ```
  Create the notary profile once with `xcrun notarytool store-credentials my-notary-profile`.
- **Folders:** an installed app saves to `~/Documents/BC Court Binder` (sample filings) and `~/Documents/BC Court Binder/Output` (binders) until you change them in the sidebar. Choices are stored in `~/.bc_court_binder_settings.json`, which is shared with a copy run from source on the same Mac.
- **No custom icon yet.** The app uses the default icon.
- `hdiutil` prints a deprecation warning when creating the image. It still works; the script can move to `diskutil image` later.

## Files

| File | Purpose |
| :--- | :--- |
| `build_dmg.sh` | Builds the app, self-tests it, signs it (optional), makes the `.dmg`, notarizes (optional) |
| `binder_app.spec` | PyInstaller specification: what goes in the bundle |
| `launcher.py` | Entry script that starts the app |

## Testing in isolation

macOS apps cannot run in a Linux container, so use one of these:

- **Sandbox on this Mac.** Mount the `.dmg` and run the self-test under `sandbox-exec` with a profile that blocks your repo, the system Python, Homebrew and the network, and a fresh `HOME`:
  ```bash
  cat > /tmp/profile.sb <<'EOF'
  (version 1)
  (allow default)
  (deny network*)
  (deny file-read* (subpath "/Users/YOU/Projects") (subpath "/Library/Frameworks/Python.framework") (subpath "/opt/homebrew") (subpath "/usr/local"))
  EOF
  hdiutil attach packaging/macos/dist/*.dmg -nobrowse -readonly -mountpoint /tmp/mnt
  mkdir -p /tmp/h && env -i HOME=/tmp/h PATH=/usr/bin:/bin TMPDIR=/tmp/h \
    sandbox-exec -f /tmp/profile.sb "/tmp/mnt/Court binder builder.app/Contents/MacOS/Court binder builder" --selftest --require-pdfcraft
  hdiutil detach /tmp/mnt
  ```
  Expect `SELFTEST OK`. Run the project's own Python under the same profile first as a control; it must be blocked.
- **A new standard user account**, or a **virtual machine** (Tart or UTM), for a real clean-machine test including the Gatekeeper experience.
