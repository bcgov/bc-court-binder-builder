# Windows installer

Builds **Court binder builder** for Windows 10/11 (64-bit) and packages it as a **WiX MSI** and a portable zip:
`dist/release/court-binder-builder-<version>-windows-x64.msi` and `...-portable.zip`. Everything the app needs is inside
(the app, the `managing-court-binders` scripts, the CSO links file, `pypdf` and Python), so people do not need Python.

The structure follows the PdfCraft packaging (`packaging/windows/` in https://github.com/richfrem/pdfcraft) and the
release process in [`docs/releasing.md`](../../docs/releasing.md): a dual-scope MSI (per-user by default), the same
PE-header, signing and MSI-inspection steps, and a portable zip. Installers are built by CI and published as GitHub
Release assets; they are never committed.

> **Status: written on a Mac and not yet run on Windows.** The PowerShell scripts parse and the PyInstaller spec was
> test-built on macOS, but the MSI has never been compiled or installed. The **Packaging build** workflow builds it
> on a clean Windows runner, installs it, self-tests the installed app, reinstalls over it and uninstalls. Treat its
> first run as the real test and fix what it finds.

## Build it

On Windows, in PowerShell 7 (`pwsh`), from the repository root:

```powershell
pwsh packaging/windows/package.ps1
```

Needs Python 3.10+ (64-bit) on `PATH` and WiX v5 (`dotnet tool install --global wix --version 5.0.2`). The script:
1. Creates its own build environment, `packaging/windows/.venv-build` (git-ignored), and installs
   `app/requirements-build.txt`.
2. Builds the app with PyInstaller (`binder_app.spec`) and checks the executable's PE header (x64, GUI subsystem).
3. Runs the packaged app's **self-test**, `Court binder builder.exe --selftest --selftest-log <file>`: a sample binder
   must pass all 20 gates. (A windowed app has no console, so the result goes to a file.)
4. Signs the executable and the MSI if a certificate is configured (`sign.ps1`).
5. Builds the MSI with WiX, then inspects the built MSI (`test-msi.ps1`).
6. Makes the portable zip.

Then `pwsh packaging/windows/test-install.ps1` installs the MSI silently for the current user, self-tests the
installed app, reinstalls over it, and uninstalls. See [`INSTALLATION.md`](INSTALLATION.md) for scopes and silent
install options.

## PdfCraft native engine

The macOS installer bundles the PdfCraft native engine. **No Windows wheel is published** for the pinned PdfCraft
release (only `macosx_11_0_arm64`), so this build omits it, and the app works the same because the binder engine does
not call PdfCraft yet. To include it, build a `win_amd64` wheel (`maturin build --release` in the PdfCraft fork, see
its `RELEASE_SDK.md`), publish it, then:

```powershell
$env:PDFCRAFT_WHEEL_URL = "https://github.com/richfrem/pdfcraft/releases/download/<tag>/<wheel>.whl"
$env:PDFCRAFT_WHEEL_SHA256 = "<the wheel's SHA-256>"     # required with a URL; PDFCRAFT_WHEEL=<local path> also works
pwsh packaging/windows/package.ps1
```

The build then checks the hash, and the self-test must also merge two PDFs with the native engine.

## Things to know

- **Unsigned by default.** A downloaded unsigned installer triggers a Microsoft Defender SmartScreen warning
  ("Windows protected your PC"): choose **More info**, then **Run anyway**. Signing needs a code-signing certificate
  or Azure Trusted Signing; see `sign.ps1` and `docs/releasing.md`. Neither path has been exercised.
- **WebView2.** The app draws its window with the Microsoft Edge WebView2 Runtime, which Windows 11 and current
  Windows 10 already have. The MSI does not check for it; if the window does not open, install the runtime from
  https://developer.microsoft.com/microsoft-edge/webview2/.
- **Scanners.** PyInstaller programs are flagged by antivirus more often than native ones; see "Scanner detections" in
  `docs/releasing.md` and `security-audit.ps1`.
- **Folders.** The app saves to `Documents\BC Court Binder` (sample filings) and `Documents\BC Court Binder\Output`
  (binders) until you change them in the sidebar. If your Documents folder is redirected by OneDrive or policy, use
  the sidebar to pick the real location.
- **64-bit Windows only.** There is no 32-bit or ARM build.

## Files

| File | Purpose |
| :--- | :--- |
| `package.ps1` | Builds the app, checks it, self-tests it, signs, builds and inspects the MSI, makes the portable zip |
| `binder_app.spec`, `launcher.py` | PyInstaller specification and entry script |
| `court-binder-builder.wxs` | WiX package: dual scope, shortcuts, harvesting the app folder |
| `installer-ui.wxs`, `install-policy.wxi` | Installer dialogs and the per-user / per-machine scope rules (adapted from PdfCraft) |
| `test-msi.ps1` | Inspects the built MSI without installing it |
| `test-install.ps1` | Silent install, self-test of the installed app, same-version upgrade, uninstall |
| `sign.ps1` | Authenticode signing from environment variables (certificate or Azure Trusted Signing; adapted from PdfCraft) |
| `security-audit.ps1` | Records the SHA-256 and signature status of files for a scanner detection (adapted from PdfCraft) |
| `INSTALLATION.md` | Scope rules and silent-install options |
