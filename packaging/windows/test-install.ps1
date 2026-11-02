<#
.SYNOPSIS
  Install the built MSI silently, self-test the installed app, reinstall over it, then uninstall.

.DESCRIPTION
  Run after package.ps1, on Windows (the packaging workflow does this on a clean runner). It proves
  that the MSI installs, that the installed app passes its self-test with nothing else installed
  for it, that installing the same version again upgrades cleanly, and that uninstall removes the
  files and the registration. Per-user is the default scope for a silent install.

.EXAMPLE
  pwsh packaging/windows/test-install.ps1
#>
param([string] $Msi)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $Msi) {
  $dist = if ($env:DIST) { $env:DIST } else { Join-Path $Root 'dist\release' }
  $found = Get-ChildItem $dist -Filter 'court-binder-builder-*-windows-*.msi' | Select-Object -First 1
  if (-not $found) { throw "No MSI in $dist. Run package.ps1 first." }
  $Msi = $found.FullName
}

$Temp = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [System.IO.Path]::GetTempPath() }
$Target = Join-Path $Temp 'cbb-installed'
if (Test-Path $Target) { Remove-Item $Target -Recurse -Force }
$Exe = Join-Path $Target 'Court binder builder.exe'

function Invoke-Msi([string] $What, [string[]] $Arguments) {
  Write-Output "==> $What"
  $log = Join-Path $Temp ("cbb-msi-" + ($What -replace '\W+', '-') + '.log')
  $p = Start-Process -FilePath msiexec.exe -Wait -PassThru -ArgumentList ($Arguments + @('/qn', '/norestart', '/l*v', "`"$log`""))
  if ($p.ExitCode -notin 0, 3010) {
    if (Test-Path $log) { Get-Content $log -Tail 40 | ForEach-Object { Write-Output "    $_" } }
    throw "$What failed (msiexec exit code $($p.ExitCode)); log: $log"
  }
}

Invoke-Msi 'install' @('/i', "`"$Msi`"", "INSTALLFOLDER=`"$Target`"", 'INSTALLDESKTOPSHORTCUT=0')
if (-not (Test-Path $Exe)) { throw "The installed app was not found at $Exe." }
if (-not (Get-ItemProperty 'HKCU:\Software\CourtBinderBuilder' -ErrorAction SilentlyContinue)) { throw 'The per-user registration is missing.' }

function Test-InstalledApp {
  Write-Output '==> self-test of the installed app'
  $log = Join-Path $Temp 'cbb-installed-selftest.log'
  if (Test-Path $log) { Remove-Item $log -Force }
  $p = Start-Process -FilePath $Exe -ArgumentList @('--selftest', '--selftest-log', $log) -Wait -PassThru
  if (Test-Path $log) { Get-Content $log | ForEach-Object { Write-Output "    $_" } }
  if ($p.ExitCode -ne 0 -or -not (Select-String -Path $log -Pattern '^SELFTEST OK' -Quiet)) {
    throw "The installed app's self-test failed (exit code $($p.ExitCode))."
  }
}
Test-InstalledApp

# Installing the same version again must upgrade in place (same-version upgrades are allowed so
# release candidates of one X.Y.Z replace each other) and leave exactly one working copy.
Invoke-Msi 'reinstall (same-version upgrade)' @('/i', "`"$Msi`"", "INSTALLFOLDER=`"$Target`"", 'INSTALLDESKTOPSHORTCUT=0')
Test-InstalledApp

Invoke-Msi 'uninstall' @('/x', "`"$Msi`"")
Start-Sleep -Seconds 2
if (Test-Path $Exe) { throw 'The app is still installed after uninstalling.' }
if (Get-ItemProperty 'HKCU:\Software\CourtBinderBuilder' -ErrorAction SilentlyContinue) { throw 'The registration is still present after uninstalling.' }

Write-Output '==> install, self-test, upgrade and uninstall all passed.'
