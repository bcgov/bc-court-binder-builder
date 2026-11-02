<#
.SYNOPSIS
  Build, sign and package Court binder builder for Windows.

.DESCRIPTION
  Produces, in $env:DIST (default: dist/release):
    court-binder-builder-<version>-windows-x64.msi            installer (WiX v5): per-user by default,
                                                              per-machine on request (see INSTALLATION.md)
    court-binder-builder-<version>-windows-x64-portable.zip   the app folder: unzip and run

  Structure follows the PdfCraft packaging (https://github.com/richfrem/pdfcraft,
  packaging/windows/package.ps1): read the version from one place, check the executable's PE
  header, sign, build the MSI, inspect the built MSI, sign it, and make a portable zip. Signing is
  delegated to sign.ps1 (skipped with a warning when no signing secrets are set).

  The app is a PyInstaller build, so unlike a native binary it carries its own Python and libraries.

  Needs: Python 3.10+ (64-bit) on PATH, and WiX v5: dotnet tool install --global wix --version 5.0.2

  PdfCraft native engine (optional, OFF by default): no Windows wheel is published for the pinned
  release (only macOS), so nothing is bundled unless you supply one:
    PDFCRAFT_WHEEL         path to a local win_amd64 wheel (for example built with maturin in ../pdfcraft)
    PDFCRAFT_WHEEL_URL     or a URL to download one; PDFCRAFT_WHEEL_SHA256 is then required
  When a wheel is bundled the self-test must also merge two PDFs with it.

  CBB_VERSION overrides the version for a test run. BUILD_PYTHON picks the Python used for the
  build environment (default: python).

.EXAMPLE
  pwsh packaging/windows/package.ps1
  pwsh packaging/windows/package.ps1 -SkipBuild   # package an existing build in packaging/windows/build
#>
param(
  [ValidateSet('x64')] [string] $Arch = 'x64',
  [switch] $SkipBuild
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$AppName = 'Court binder builder'
$Python = if ($env:BUILD_PYTHON) { $env:BUILD_PYTHON } else { 'python' }

function Invoke-Native([string] $What, [scriptblock] $Block) {
  Write-Output "==> $What"
  & $Block
  if ($LASTEXITCODE -ne 0) { throw "$What failed with exit code $LASTEXITCODE" }
}

# The version lives in one place: __version__ in app/binder_app/__init__.py.
$Version = $env:CBB_VERSION
if (-not $Version) {
  foreach ($line in Get-Content (Join-Path $Root 'app\binder_app\__init__.py')) {
    if ($line -match '^__version__\s*=\s*"([^"]+)"') { $Version = $Matches[1]; break }
  }
}
if (-not $Version) { throw 'could not read __version__ from app/binder_app/__init__.py' }
# MSI ProductVersion is numeric (major.minor.build); pre-release tags are dropped there.
$MsiVersion = ($Version -split '-')[0]

$Dist = if ($env:DIST) { $env:DIST } else { Join-Path $Root 'dist\release' }
New-Item -ItemType Directory -Force -Path $Dist | Out-Null
$Work = Join-Path $PSScriptRoot 'build'
$Venv = Join-Path $PSScriptRoot '.venv-build'
$AppDir = Join-Path $Work "dist\$AppName"
$AppExe = Join-Path $AppDir "$AppName.exe"

Write-Output "$AppName $Version for Windows $Arch"

# ---- build -------------------------------------------------------------------------------------
$WithPdfCraft = $false
if (-not $SkipBuild) {
  if (Test-Path $Work) { Remove-Item $Work -Recurse -Force }
  New-Item -ItemType Directory -Path $Work | Out-Null

  Write-Output "==> Preparing the build environment ($Venv)"
  if (-not (Test-Path (Join-Path $Venv 'Scripts\python.exe'))) {
    Invoke-Native 'creating the virtual environment' { & $Python -m venv $Venv }
  }
  $VenvPython = Join-Path $Venv 'Scripts\python.exe'
  Invoke-Native 'upgrading pip' { & $VenvPython -m pip install --quiet --upgrade pip }
  Invoke-Native 'installing the build requirements' { & $VenvPython -m pip install --quiet -r (Join-Path $Root 'app\requirements-build.txt') }

  $Wheel = $env:PDFCRAFT_WHEEL
  if (-not $Wheel -and $env:PDFCRAFT_WHEEL_URL) {
    if (-not $env:PDFCRAFT_WHEEL_SHA256) { throw 'PDFCRAFT_WHEEL_URL needs PDFCRAFT_WHEEL_SHA256.' }
    $Wheel = Join-Path $Work ([System.IO.Path]::GetFileName(([uri]$env:PDFCRAFT_WHEEL_URL).AbsolutePath))
    Write-Output '==> Downloading the PdfCraft wheel'
    Invoke-WebRequest -Uri $env:PDFCRAFT_WHEEL_URL -OutFile $Wheel
  }
  if ($Wheel) {
    if ($env:PDFCRAFT_WHEEL_SHA256) {
      $actual = (Get-FileHash $Wheel -Algorithm SHA256).Hash.ToLowerInvariant()
      if ($actual -ne $env:PDFCRAFT_WHEEL_SHA256.ToLowerInvariant()) {
        throw "PdfCraft wheel hash mismatch: expected $($env:PDFCRAFT_WHEEL_SHA256), got $actual. Refusing to bundle it."
      }
      Write-Output '    SHA-256 verified'
    }
    Invoke-Native 'installing the PdfCraft wheel' { & $VenvPython -m pip install --quiet --no-deps --force-reinstall $Wheel }
    $WithPdfCraft = $true
  }
  else {
    Write-Output '==> No PdfCraft wheel supplied: building without the native engine (none is published for Windows yet)'
    & $VenvPython -m pip uninstall --quiet -y pdfcraft 2>$null
  }

  Invoke-Native "PyInstaller ($AppName)" {
    & $VenvPython -m PyInstaller --noconfirm --clean --distpath (Join-Path $Work 'dist') --workpath (Join-Path $Work 'pyinstaller') (Join-Path $PSScriptRoot 'binder_app.spec')
  }
}
if (-not (Test-Path $AppExe)) { throw "$AppExe not found (run without -SkipBuild)" }

# Check the executable's PE header before packaging. Machine (COFF header) must match -Arch, so an
# x64 build can never ship labelled for another processor. Subsystem (optional header): 2 = Windows
# GUI, 3 = console. The app must be GUI: no console window may open with it (the PdfCraft packaging
# checks the same, #57).
function Get-PeHeader([string] $Path) {
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  $pe = [BitConverter]::ToInt32($bytes, 0x3C)
  return @{ Machine = [BitConverter]::ToUInt16($bytes, $pe + 4); Subsystem = [BitConverter]::ToUInt16($bytes, $pe + 0x5C) }
}
$h = Get-PeHeader $AppExe
if ($h.Machine -ne 0x8664) { throw "$AppName.exe is for machine 0x$('{0:X}' -f $h.Machine), expected 0x8664 (x64)" }
if ($h.Subsystem -ne 2) { throw "$AppName.exe has PE subsystem $($h.Subsystem), expected 2 (Windows GUI)" }
Write-Output "ok $AppName.exe`: x64, PE subsystem $($h.Subsystem)"

# ---- self-test of the packaged app (no window) ------------------------------------------------
# A windowed app has no console, so the result goes to a file.
$Log = Join-Path $Work 'selftest.log'
if (Test-Path $Log) { Remove-Item $Log -Force }
$SelfArgs = @('--selftest', '--selftest-log', $Log)
if ($WithPdfCraft) { $SelfArgs += '--require-pdfcraft' }
Write-Output '==> self-test of the packaged app'
$proc = Start-Process -FilePath $AppExe -ArgumentList $SelfArgs -Wait -PassThru
if (Test-Path $Log) { Get-Content $Log | ForEach-Object { Write-Output "    $_" } }
if ($proc.ExitCode -ne 0 -or -not (Test-Path $Log) -or -not (Select-String -Path $Log -Pattern '^SELFTEST OK' -Quiet)) {
  throw "The packaged app's self-test failed (exit code $($proc.ExitCode))."
}

# ---- stage and sign ----------------------------------------------------------------------------
$Stage = Join-Path $Work "stage\$AppName"
Remove-Item -Recurse -Force $Stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path (Split-Path $Stage) | Out-Null
Copy-Item -Recurse $AppDir $Stage
foreach ($f in 'LICENSE.md', 'README.md') {
  $p = Join-Path $Root $f
  if (Test-Path $p) { Copy-Item $p $Stage }
}
& (Join-Path $PSScriptRoot 'sign.ps1') (Join-Path $Stage "$AppName.exe")

# ---- MSI ---------------------------------------------------------------------------------------
$Msi = Join-Path $Dist "court-binder-builder-$Version-windows-$Arch.msi"
Invoke-Native 'wix build' {
  wix build (Join-Path $PSScriptRoot 'court-binder-builder.wxs') -arch $Arch `
    (Join-Path $PSScriptRoot 'installer-ui.wxs') `
    -d "Version=$MsiVersion" -d "AppDir=$Stage" `
    -o $Msi
}
# Inspect the built MSI, not just the XML, before signing/publishing it. In a child process, so
# its Windows Installer database handle is gone before signtool opens the MSI.
Invoke-Native 'test-msi' {
  & (Get-Process -Id $PID).Path -NoProfile -File (Join-Path $PSScriptRoot 'test-msi.ps1') $Msi -ExpectedVersion $MsiVersion
}
# wix writes its debug symbols (.wixpdb) next to the MSI; keep them out of the release assets.
Remove-Item -Force -ErrorAction SilentlyContinue ([IO.Path]::ChangeExtension($Msi, '.wixpdb'))
& (Join-Path $PSScriptRoot 'sign.ps1') $Msi

# ---- portable zip ------------------------------------------------------------------------------
$Portable = Join-Path $Work "court-binder-builder-$Version-windows-$Arch-portable"
Remove-Item -Recurse -Force $Portable -ErrorAction SilentlyContinue
Copy-Item -Recurse $Stage $Portable
$Zip = Join-Path $Dist "court-binder-builder-$Version-windows-$Arch-portable.zip"
Remove-Item -Force $Zip -ErrorAction SilentlyContinue
Compress-Archive -Path $Portable -DestinationPath $Zip

Get-Item $Msi, $Zip | Format-Table Name, Length
