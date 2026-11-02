# Releasing Court binder builder

How the installers are built, signed and published. The approach follows the PdfCraft release process
(`docs/releasing.md` in https://github.com/richfrem/pdfcraft): installers are **never committed**; CI builds
them on clean runners and attaches them to a GitHub Release together with `SHA256SUMS.txt`.

## Cutting a release

1. **Bump the version** on `main`. It lives only in `__version__` in `app/binder_app/__init__.py`.
   Commit the change through the normal review flow.
2. **Merge `main` into `release`** (or fast-forward it) and push. The **Release** workflow starts by itself.
3. **Wait for the draft.** When every job has finished (notarization is the slow part), the Releases page has a
   draft `Court binder builder vX.Y.Z` with the Mac `.dmg`, the Windows `.msi` and portable `.zip`, and
   `SHA256SUMS.txt`.
4. **Check it.** Download an installer or two and read the job summaries. A `::warning::` there means a signing
   secret was missing and that artifact is unsigned.
5. **Publish** the draft in the GitHub UI. Publishing creates the `vX.Y.Z` tag. Versions with a suffix
   (`0.2.0-rc.1`) are marked as pre-releases.

Pushing to `release` again before you publish rebuilds the draft and replaces its assets. Once the draft is
published, the workflow refuses to touch that version; bump it first.

**Test runs & manual release:** *Actions > Release > Run workflow* runs the pipeline by hand. The optional `version` input
(such as `0.2.0-rc.1`) overrides `__version__` for that run only. Run it with `dry_run: true` for a
**dry run**: the installers are built and tested, and no draft is created. With `dry_run: false` (default),
a draft release is created or updated on GitHub with the macOS `.dmg`, Windows `.msi` and portable `.zip`, and `SHA256SUMS.txt`.

Pull requests that touch `packaging/`, `app/` or the skill scripts run **Packaging build** (both installers,
unsigned) and **Packaging lint**, so installer problems show up before a release.

## What gets built

All names are `court-binder-builder-<version>-<os>-<arch>.<ext>`.

| Artifact | Built by | Notes |
| :--- | :--- | :--- |
| `...-macos-arm64.dmg` | `packaging/macos/package.sh` on a macOS runner | Drag-to-Applications image with a branded window. One build per processor type (PyInstaller cannot cross-build). |
| `...-windows-x64.msi` | `packaging/windows/package.ps1` on a Windows runner | WiX v5 package: per-user by default, per-machine on request; Start menu and desktop shortcuts; same-version upgrades allowed. |
| `...-windows-x64-portable.zip` | same | The app folder: unzip and run. |
| `SHA256SUMS.txt` | the release job | Checksums of every artifact. |

### macOS

`package.sh` builds the app with PyInstaller, then signs it **inside out**: every Mach-O file in the bundle with
the hardened runtime and the entitlements in `entitlements.plist`, then the bundle (no `--deep` on the final
signature). It runs the packaged app's self-test (a sample binder must pass all 20 gates, and the bundled PdfCraft
engine must merge two PDFs), builds the DMG with a plain `hdiutil create -srcfolder` (with retries), signs it, and
checks that the app **inside the mounted image** still passes `codesign --verify --strict`. With a real identity
and Apple credentials it also notarizes the app and the DMG and staples the tickets (retrying Apple's flaky
ticket fetch). Without them it signs ad hoc and warns.

The DMG window (background and icon layout) comes from static files in `packaging/macos/dmg/`; see its README.

### Windows

`package.ps1` builds the app with PyInstaller, reads the executable's PE header (it must be x64 and a GUI-subsystem
program, so no console window opens), runs the self-test, signs the executable, builds the MSI with WiX, inspects
the **built MSI** (`test-msi.ps1`: version, upgrade code, icon id, file count, shortcuts), signs it, and makes the
portable zip. The workflow then runs `test-install.ps1`: install silently, self-test the installed app, reinstall
over it (a same-version upgrade) and uninstall, checking the files and registration are gone. See
`packaging/windows/INSTALLATION.md` for the scope rules.

### PdfCraft native engine

The macOS build bundles the PdfCraft native engine (a pinned, SHA-256-checked wheel). No Windows wheel is
published, so the Windows build omits it unless a `win_amd64` wheel is supplied through `PDFCRAFT_WHEEL` or
`PDFCRAFT_WHEEL_URL` + `PDFCRAFT_WHEEL_SHA256`. The binder engine does not call PdfCraft yet either way.

## Secrets

The signing secrets live in the repository's **`release` environment** (*Settings > Environments > release*),
which you should restrict to the `release` branch. The macOS, Windows and draft-release jobs declare
`environment: release`. Each secret is optional: if one is missing, that platform's artifacts are unsigned and the
run shows a warning.

| Secret | Used for |
| :--- | :--- |
| `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD` | base64 Developer ID Application `.p12` and its password |
| `KEYCHAIN_PASSWORD` | the temporary CI keychain (random if unset) |
| `APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID` | `notarytool` (an app-specific password) |
| `WINDOWS_CERTIFICATE`, `WINDOWS_CERTIFICATE_PASSWORD` | base64 `.pfx` code-signing certificate and its password |
| `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` | service principal for Azure Trusted Signing (instead of a `.pfx`) |
| `AZURE_SIGNING_ENDPOINT`, `AZURE_SIGNING_ACCOUNT`, `AZURE_CERT_PROFILE` | Trusted Signing endpoint, account and certificate profile |

`GITHUB_TOKEN` creates the release; only the final job gets `contents: write`. Neither signing path has been
exercised for this project yet (no certificates exist), so treat the first signed release as a test.

## Checks

`.github/workflows/packaging-lint.yml` runs on changes to `packaging/` and the workflows: actionlint, shellcheck,
a PowerShell parse, xmllint (WiX and plist) and the MSI icon-id check. `.github/workflows/packaging-build.yml`
builds and tests both installers on pull requests.

## Scanner detections

This app is a **PyInstaller** program: it carries its own Python and libraries, and antivirus and reputation
scanners flag such programs more often than small native ones. A detection is not proof of anything. Before you
change code or answer publicly:

1. **Confirm the file is the release.** Compare its SHA-256 with `SHA256SUMS.txt` on the GitHub Release. Only a
   file whose hash matches says anything about that release.
2. **Record the signature.** `packaging/windows/security-audit.ps1` prints the Authenticode status:
   - `Valid`: the signature verifies.
   - `NotSigned`: no signature, as in developer and test builds. Not evidence of compromise by itself, but it is
     the main reason for Defender SmartScreen warnings.
   - `HashMismatch`: the file changed after it was signed. Investigate.
   - `NotTrusted` or `UnknownError`: a signature exists but did not validate on this machine. Compare the signer
     and the hash with the release.
3. **Prefer signed, checksummed releases.** Signing and published checksums are the real defence against false
   positives; for a flagged build, submit the file to the scanner vendor's false-positive process and say which
   release and hash it is.
