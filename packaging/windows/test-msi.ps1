<#
.SYNOPSIS
  Check the compiled MSI's metadata, icon, shortcuts and files, without installing it.

.DESCRIPTION
  Reads the Windows Installer database with the WindowsInstaller COM object, so it needs Windows.
  The approach follows the PdfCraft packaging's test-msi.ps1 (https://github.com/richfrem/pdfcraft),
  with checks for this package. A real install, self-test and uninstall is in test-install.ps1.

.EXAMPLE
  pwsh packaging/windows/test-msi.ps1 dist/release/court-binder-builder-0.1.0-windows-x64.msi -ExpectedVersion 0.1.0
#>
param(
  [Parameter(Mandatory)] [string] $Path,
  [Parameter(Mandatory)] [string] $ExpectedVersion
)
$ErrorActionPreference = 'Stop'
$Installer = New-Object -ComObject WindowsInstaller.Installer
$Database = $Installer.OpenDatabase((Resolve-Path -LiteralPath $Path).Path, 0)

function Get-Values([string] $Sql, [int] $Column = 1) {
  $view = $Database.OpenView($Sql)
  try {
    [void] $view.Execute()
    $values = @()
    while ($record = $view.Fetch()) { $values += $record.StringData($Column) }
    return , $values
  }
  finally { [void] $view.Close() }
}

function Get-Property([string] $Name) {
  $v = Get-Values "SELECT ``Value`` FROM ``Property`` WHERE ``Property`` = '$Name'"
  if ($v.Count -ne 1) { throw "MSI property missing: $Name" }
  return $v[0]
}

function Assert-Equal($Actual, $Expected, [string] $What) {
  if ($Actual -cne $Expected) { throw "$What`: expected '$Expected', got '$Actual'" }
}

Assert-Equal (Get-Property 'ProductName') 'Court binder builder' 'MSI product name'
Assert-Equal (Get-Property 'Manufacturer') 'bc-court-binder-builder project' 'MSI manufacturer'
Assert-Equal (Get-Property 'ProductVersion') $ExpectedVersion 'MSI version'
Assert-Equal (Get-Property 'UpgradeCode') '{96FC72AE-B00C-45EA-AAB5-D197B6123596}' 'MSI upgrade code'

# Windows Installer needs an icon id ending in .ico or .exe, or shortcuts and Add/Remove Programs
# show a blank icon.
$icons = Get-Values 'SELECT `Name` FROM `Icon`'
if ($icons.Count -lt 1) { throw 'the MSI has no icon' }
foreach ($icon in $icons) {
  if ($icon -notmatch '\.(ico|exe)$') { throw "MSI icon id must end in .ico or .exe: $icon" }
}

$files = Get-Values 'SELECT `FileName` FROM `File`'
if (-not ($files | Where-Object { $_ -like '*Court binder builder.exe' })) { throw 'the MSI does not contain Court binder builder.exe' }
# A PyInstaller folder holds hundreds of files; a handful means the harvest went wrong.
if ($files.Count -lt 50) { throw "the MSI holds only $($files.Count) files; the app folder was not harvested" }

$shortcuts = Get-Values 'SELECT `Name` FROM `Shortcut`'
if ($shortcuts.Count -ne 2) { throw "expected 2 shortcuts (Start menu, desktop), found $($shortcuts.Count)" }

$appPaths = Get-Values 'SELECT `Key` FROM `Registry`' | Where-Object { $_ -like '*App Paths\Court binder builder.exe' }
if (-not $appPaths) { throw 'the MSI has no App Paths registration' }

Write-Output "ok MSI: $($files.Count) files, $($shortcuts.Count) shortcuts, version $ExpectedVersion"
