# Code signing Court binder builder for Windows

How to sign **Court binder builder** (`Court binder builder.exe` and the `.msi` installer) using Authenticode code signing.

---

## 1. Why Code Signing Matters

- **Eliminates SmartScreen Warnings:** Unsigned executables and newly compiled releases trigger Microsoft Defender SmartScreen warnings (*"Windows protected your PC"*, *"isn't commonly downloaded"*).
- **Verified Publisher Identity:** Replaces the generic *"Unknown Publisher"* UAC prompt with a verified organization or developer name.
- **Dual-Layer Signing:** The packaging process signs both:
  1. The internal executable: `Court binder builder.exe` (staged before WiX packaging and portable zip creation).
  2. The installer database: `court-binder-builder-<version>-windows-x64.msi`.

---

## 2. Prerequisites on Windows

When building and signing on a Windows computer:

1. **Python 3.10+ (64-bit)** on `PATH`.
2. **WiX v5 Toolchain:**
   ```powershell
   dotnet tool install --global wix --version 5.0.2
   ```
3. **Windows 10/11 SDK (for `signtool.exe`):**
   `signtool.exe` is required by `packaging/windows/sign.ps1`. It is installed automatically with Visual Studio (Desktop C++ workload) or via the standalone [Windows SDK installer](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/). Ensure `signtool.exe` is on your `PATH` or located under `C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64`.

---

## 3. Local Development: Self-Signing on Your Windows Machine

For local development and testing, you can generate a self-signed code-signing certificate and trust it in your local certificate store. Once added to `Cert:\CurrentUser\Root`, Windows will treat your builds as signed by a trusted publisher on your machine.

### Step 1: Create and Trust a Local Code-Signing Certificate

Run this in an elevated or standard PowerShell session:

```powershell
# 1. Create a self-signed code-signing certificate in your personal store
$cert = New-SelfSignedCertificate `
  -Type CodeSigningCert `
  -Subject "CN=Court Binder Builder Local" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -KeySpec Signature

# 2. Add it to your Trusted Root Certification Authorities store
$rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
$rootStore.Open("ReadWrite")
$rootStore.Add($cert)
$rootStore.Close()

Write-Host "Certificate created and trusted: $($cert.Thumbprint)" -ForegroundColor Green
```

### Step 2: Build and Sign the MSI in One Step

The repository's `packaging/windows/package.ps1` script automatically delegates signing to `sign.ps1`. It reads the signing certificate from `$env:WINDOWS_CERTIFICATE` (base64-encoded `.pfx`) and `$env:WINDOWS_CERTIFICATE_PASSWORD`.

Run this script from the repository root to export your certificate to memory, set the environment variables, and build the signed MSI:

```powershell
# 1. Grab your local code-signing cert
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
  Where-Object { $_.Subject -match "Court Binder Builder" } |
  Select-Object -First 1

if (-not $cert) { throw "No code-signing certificate found in Cert:\CurrentUser\My" }

# 2. Export to a temporary .pfx and set build environment variables
$tempPass = "LocalSignTemp123!"
$securePass = ConvertTo-SecureString $tempPass -AsPlainText -Force
$tempPfx = Join-Path $env:TEMP "temp_dev_signer.pfx"

Export-PfxCertificate -Cert $cert -FilePath $tempPfx -Password $securePass | Out-Null
$env:WINDOWS_CERTIFICATE = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tempPfx))
$env:WINDOWS_CERTIFICATE_PASSWORD = $tempPass
Remove-Item $tempPfx -Force

# 3. Build, self-test, WiX package, and sign the MSI + portable zip
pwsh packaging/windows/package.ps1
```

### Step 3: Verify the Built Installer

Run the repository's security audit script:

```powershell
pwsh packaging/windows/security-audit.ps1 dist/release/court-binder-builder-*-windows-x64.msi
```

Expected output:
```text
court-binder-builder-0.1.0-windows-x64.msi: Valid (Court Binder Builder Local, SHA256)
```

---

## 4. Alternative: Signing an Existing or Pre-Built MSI

If you already have a compiled `.msi` file (e.g., downloaded from a CI artifact or built without signing secrets) and want to sign it directly:

### Option A: Using PowerShell's `Set-AuthenticodeSignature` (No SDK Required)

```powershell
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1

# Sign the MSI
Set-AuthenticodeSignature `
  -FilePath .\dist\release\court-binder-builder-0.1.0-windows-x64.msi `
  -Certificate $cert `
  -TimestampServer "http://timestamp.digicert.com" `
  -HashAlgorithm SHA256
```

### Option B: Using `signtool.exe` Directly

```powershell
signtool sign /v /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /s My /n "Court Binder Builder Local" .\dist\release\court-binder-builder-0.1.0-windows-x64.msi
```

---

## 5. Production Signing in CI (GitHub Actions)

For public releases distributed to end-users without manual certificate installation, the repository supports two automated signing backends in `.github/workflows/release.yml`:

### Method 1: Azure Trusted Signing (Recommended)
Set the following secrets in GitHub repository settings (*Settings > Secrets and variables > Actions* or Environment *release*):
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_SIGNING_ENDPOINT` (e.g. `https://eus.codesigning.azure.net`)
- `AZURE_SIGNING_ACCOUNT`
- `AZURE_CERT_PROFILE`

### Method 2: Standard Authenticode PFX Certificate
Set the following secrets:
- `WINDOWS_CERTIFICATE`: Base64-encoded string of your `.pfx` certificate file (`[Convert]::ToBase64String([IO.File]::ReadAllBytes("cert.pfx"))`).
- `WINDOWS_CERTIFICATE_PASSWORD`: Password for the `.pfx` certificate.

When either set of secrets is present, the GitHub Actions release workflow signs both the executable and MSI automatically during CI execution.
