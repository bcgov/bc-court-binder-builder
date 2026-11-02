# Windows installation scope and silent installs

The MSI follows the PdfCraft install policy (`packaging/windows/INSTALLATION.md` and `install-policy.wxi` in
https://github.com/richfrem/pdfcraft), with names changed for Court binder builder.

- **Default: only for the current user.** A new install goes to `%LOCALAPPDATA%\Programs\Court binder builder`
  and needs no administrator rights. The first page of the full-UI installer offers **Everyone on this computer**
  instead (asks an administrator, installs to `Program Files\Court binder builder`).
- **Updates keep the existing context and folder.** Installing a newer version (or the same version again) over an
  existing copy upgrades it in place. A copy installed for one account is not moved to everyone, or the other way
  round: the installer refuses and asks you to uninstall the old copy first.
- **Same-version upgrades are allowed**, so release candidates of one `X.Y.Z` replace each other (MSI versions are
  numeric; `0.2.0-rc.1` and `0.2.0-rc.2` are both `0.2.0`).
- **Shortcuts:** a Start menu entry and, by default, a desktop shortcut (a checkbox on the first page). Deleting
  the desktop shortcut once keeps it away on later updates.

## Silent installs (for IT)

```powershell
# Per user (default), no administrator needed
msiexec /i court-binder-builder-<version>-windows-x64.msi /qn

# For everyone on the computer (run elevated)
msiexec /i court-binder-builder-<version>-windows-x64.msi /qn ALLUSERS=1

# Options
#   INSTALLFOLDER="D:\Apps\Court binder builder"   explicit folder (never replaced by an update)
#   INSTALLDESKTOPSHORTCUT=0                        no desktop shortcut

# Uninstall (use the same MSI)
msiexec /x court-binder-builder-<version>-windows-x64.msi /qn
```

Add `/l*v install.log` to any command to write a log.

## What is checked, and what is not

`test-msi.ps1` inspects the built MSI (version, upgrade code, icon, files, shortcuts) and `test-install.ps1`
installs it silently for the current user, self-tests the installed app, reinstalls over it and uninstalls (run by
the packaging workflows on a clean Windows runner). **Not yet tested:** the per-machine scope, the full-UI wizard,
the scope-conflict refusals, rollback and cancellation, and upgrades from older versions. Those need an
authorised clean Windows machine.
