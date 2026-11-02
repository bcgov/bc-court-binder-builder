#!/usr/bin/env bash
# Build, sign and (optionally) notarize the macOS release artifact:
#
#   $DIST/court-binder-builder-<version>-macos-<arch>.dmg    Court binder builder.app on a drag-to-Applications DMG
#
# Usage: packaging/macos/package.sh [--skip-build]
#
# Structure and safeguards follow the PdfCraft packaging (https://github.com/richfrem/pdfcraft,
# packaging/macos/package.sh): hardened-runtime signing, notarization with retries, a DMG made with
# a plain `hdiutil create -srcfolder`, and a check that the app inside the image still passes
# `codesign --verify --strict`.
#
# The app is built for the processor type of the Mac that runs this (PyInstaller cannot cross-build).
#
# Environment:
#   MACOS_SIGN_IDENTITY   codesign identity (name or SHA-1). Default "-" = ad-hoc (fine on this Mac;
#                         Gatekeeper rejects it on other Macs). In CI, import-cert.sh sets it.
#   MACOS_KEYCHAIN        keychain holding the identity (optional)
#   APPLE_ID, APPLE_PASSWORD (app-specific password), APPLE_TEAM_ID
#                         all three, and a real identity, enable notarization
#   CBB_VERSION           override the version for a test run
#   DIST                  output directory (default: dist/release)
#
# PdfCraft native engine (on by default; this is the build-time equivalent of
#   pip install "<wheel url>" so users never run pip):
#   PDFCRAFT_WHEEL_URL     wheel to download (default: the v0.16.1 release, Python 3.13, Apple Silicon)
#   PDFCRAFT_WHEEL_SHA256  its expected SHA-256 (default: the pinned release hash)
#   PDFCRAFT_WHEEL         use a local wheel instead (hash checked only if PDFCRAFT_WHEEL_SHA256 is set)
#   WITH_PDFCRAFT=0        build without it
#   BUILD_PYTHON           Python used to create the build environment (default python3)
set -euo pipefail
# shellcheck source=../env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
HERE="$ROOT/packaging/macos"

SKIP_BUILD=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build) SKIP_BUILD=1; shift ;;
    -h | --help) sed -n '2,31p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

APP_NAME="Court binder builder"
ARCH="$(uname -m)"
IDENTITY="${MACOS_SIGN_IDENTITY:--}"
WORK="$HERE/build"
VENV="${BUILD_VENV:-$HERE/.venv-build}"
APP="$WORK/dist/$APP_NAME.app"
DMG="$DIST/court-binder-builder-$VERSION-macos-$ARCH.dmg"
WITH_PDFCRAFT="${WITH_PDFCRAFT:-1}"
PDFCRAFT_WHEEL_URL="${PDFCRAFT_WHEEL_URL:-https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl}"
PDFCRAFT_DEFAULT_SHA256="53f52d2f154d723c50836c2820f9ce19fb4bc9f0c2bd88c48f1b8e3b2a364f46"

NOTARIZE=0
if [[ "$IDENTITY" = "-" ]]; then
  warn "macOS: ad-hoc signing (no MACOS_SIGN_IDENTITY); the artifact is not notarized"
elif [[ -n "${APPLE_ID:-}" ]] && [[ -n "${APPLE_PASSWORD:-}" ]] && [[ -n "${APPLE_TEAM_ID:-}" ]]; then
  NOTARIZE=1
else
  warn "macOS: APPLE_ID / APPLE_PASSWORD / APPLE_TEAM_ID incomplete; signed but not notarized"
fi

echo "==> $APP_NAME $VERSION for macOS ($ARCH), identity: $IDENTITY, notarize: $NOTARIZE"

# ---- build -------------------------------------------------------------------------------------
if [[ "$SKIP_BUILD" = 0 ]]; then
  rm -rf "$WORK"
  mkdir -p "$WORK"

  echo "==> Preparing the build environment ($VENV)"
  if [[ ! -x "$VENV/bin/python" ]]; then
    "${BUILD_PYTHON:-python3}" -m venv "$VENV"
  fi
  "$VENV/bin/python" -m pip install -q --upgrade pip
  "$VENV/bin/python" -m pip install -q -r "$ROOT/app/requirements-build.txt"

  if [[ "$WITH_PDFCRAFT" = "1" ]]; then
    if [[ -n "${PDFCRAFT_WHEEL:-}" ]]; then
      WHEEL="$PDFCRAFT_WHEEL"
      EXPECTED="${PDFCRAFT_WHEEL_SHA256:-}"
      echo "==> Using local PdfCraft wheel: $WHEEL"
    else
      mkdir -p "$WORK/wheel"
      WHEEL="$WORK/wheel/$(basename "$PDFCRAFT_WHEEL_URL")"
      EXPECTED="${PDFCRAFT_WHEEL_SHA256:-$PDFCRAFT_DEFAULT_SHA256}"
      echo "==> Downloading the PdfCraft wheel"
      curl -fL --silent --show-error -o "$WHEEL" "$PDFCRAFT_WHEEL_URL"
    fi
    if [[ -n "$EXPECTED" ]]; then
      ACTUAL="$(shasum -a 256 "$WHEEL" | awk '{print $1}')"
      if [[ "$ACTUAL" != "$EXPECTED" ]]; then
        echo "error: PdfCraft wheel hash mismatch: expected $EXPECTED, got $ACTUAL. Refusing to bundle it." >&2
        exit 1
      fi
      echo "    SHA-256 verified"
    fi
    echo "==> Installing the PdfCraft wheel into the build environment"
    "$VENV/bin/python" -m pip install -q --no-deps --force-reinstall "$WHEEL"
  else
    echo "==> Building without the PdfCraft native engine (WITH_PDFCRAFT=0)"
    "$VENV/bin/python" -m pip uninstall -q -y pdfcraft 2>/dev/null || true
  fi

  echo "==> Building $APP_NAME.app with PyInstaller"
  "$VENV/bin/pyinstaller" --noconfirm --clean --distpath "$WORK/dist" --workpath "$WORK/pyinstaller" "$HERE/binder_app.spec"
fi

if [[ ! -d "$APP" ]]; then
  echo "error: $APP not found (run without --skip-build)" >&2
  exit 1
fi

# ---- signing helpers ---------------------------------------------------------------------------
sign() {
  # Hardened runtime + secure timestamp for a real identity; ad-hoc can't be timestamped.
  local ts=(--timestamp)
  [[ "$IDENTITY" = "-" ]] && ts=(--timestamp=none)
  local kc=()
  [[ -n "${MACOS_KEYCHAIN:-}" ]] && kc=(--keychain "$MACOS_KEYCHAIN")
  codesign --force --sign "$IDENTITY" ${kc[@]+"${kc[@]}"} "${ts[@]}" "$@"
}

# `stapler staple` and `stapler validate` both fetch the ticket from Apple's CloudKit, and a dropped
# connection there fails them although notarization worked. Both are idempotent, so retry with a
# pause; a missing or bad ticket still fails every try.
stapler_retry() {
  local try
  for try in 1 2 3 4; do
    xcrun stapler "$1" "$2" && return 0
    [[ "$try" = 4 ]] && break
    echo "stapler $1 failed (try $try of 4); retrying in $((try * 20)) s" >&2
    sleep $((try * 20))
  done
  echo "error: stapler $1 $(basename "$2") failed 4 times" >&2
  exit 1
}

notarize() {
  local file="$1" out id status
  echo "==> notarizing $(basename "$file") (this can take a few minutes)"
  out="$(xcrun notarytool submit "$file" --apple-id "$APPLE_ID" --password "$APPLE_PASSWORD" \
    --team-id "$APPLE_TEAM_ID" --wait --timeout 1h --output-format json)" || true
  echo "$out"
  id="$(printf '%s' "$out" | plutil -extract id raw -o - - 2>/dev/null || true)"
  status="$(printf '%s' "$out" | plutil -extract status raw -o - - 2>/dev/null || true)"
  if [[ "$status" != "Accepted" ]]; then
    if [[ -n "$id" ]]; then
      xcrun notarytool log "$id" --apple-id "$APPLE_ID" --password "$APPLE_PASSWORD" --team-id "$APPLE_TEAM_ID" || true
    fi
    echo "error: notarization of $(basename "$file") failed (status: ${status:-unknown})" >&2
    exit 1
  fi
}

# ---- sign the app, inside out ------------------------------------------------------------------
# A PyInstaller bundle holds many separate Mach-O files (Python, extension modules, libraries).
# Sign every one with the hardened runtime first, deepest paths first, then the bundle itself
# (no --deep on the final signature), as the PdfCraft packaging does for its binaries.
echo "==> signing the app (hardened runtime)"
COUNT=0
while IFS= read -r file; do
  if file -b "$file" | grep -q "Mach-O"; then
    sign --options runtime --entitlements "$HERE/entitlements.plist" "$file"
    COUNT=$((COUNT + 1))
  fi
done < <(find "$APP/Contents" -type f ! -path "$APP/Contents/MacOS/$APP_NAME" -print |
  awk '{ print length($0) "\t" $0 }' | sort -rn | cut -f2-)
echo "    signed $COUNT nested files"
sign --options runtime --entitlements "$HERE/entitlements.plist" "$APP/Contents/MacOS/$APP_NAME"
sign --options runtime --entitlements "$HERE/entitlements.plist" "$APP"
codesign --verify --strict --deep --verbose=2 "$APP"

# ---- self-test (no window) ---------------------------------------------------------------------
echo "==> self-test of the packaged app (no window)"
SELFTEST_ARGS=(--selftest)
[[ "$WITH_PDFCRAFT" = "1" ]] && SELFTEST_ARGS+=(--require-pdfcraft)
"$APP/Contents/MacOS/$APP_NAME" "${SELFTEST_ARGS[@]}"

if [[ "$NOTARIZE" = 1 ]]; then
  ditto -c -k --keepParent "$APP" "$WORK/notarize.zip"
  notarize "$WORK/notarize.zip"
  stapler_retry staple "$APP"
  stapler_retry validate "$APP"
  spctl --assess --type execute -vvv "$APP"
fi

# ---- DMG ---------------------------------------------------------------------------------------
echo "==> building $DMG"
STAGE="$WORK/dmg"
rm -rf "$STAGE"
mkdir -p "$STAGE"
ditto "$APP" "$STAGE/$APP_NAME.app"
ln -s /Applications "$STAGE/Applications"
# Finder window layout: background, icon size and positions (packaging/macos/dmg/README.md).
mkdir -p "$STAGE/.background"
cp "$HERE/dmg/background.tiff" "$STAGE/.background/background.tiff"
cp "$HERE/dmg/dmg-layout.DS_Store" "$STAGE/.DS_Store"
rm -f "$DMG"
# `hdiutil create -srcfolder` writes the files as they are. `makehybrid -hfs` gave every file a
# com.apple.FinderInfo, which `codesign --verify --strict` rejects as "Finder information, or
# similar detritus" on the app in the image (PdfCraft #390). `create` attaches a device while it
# copies, which fails now and then on CI runners ("Resource busy"), so it gets a few tries. The
# volume name has no version: .DS_Store finds the background through an alias that includes it.
hdiutil_retry() {
  local what="$1" attempt
  shift
  for attempt in 1 2 3 4 5; do
    if hdiutil "$@"; then
      return 0
    fi
    [[ "$attempt" = 5 ]] && { echo "hdiutil $what failed 5 times" >&2; return 1; }
    warn "hdiutil $what failed (attempt $attempt of 5); retrying in $((attempt * 10))s"
    sleep $((attempt * 10))
  done
}
hdiutil_retry create create -srcfolder "$STAGE" -volname "$APP_NAME" -fs HFS+ -format UDZO -imagekey zlib-level=9 -ov "$DMG"
sign "$DMG"
codesign --verify --strict --verbose=2 "$DMG"
# The app inside the image must still pass --strict, so a detritus regression can't ship.
MOUNT="$WORK/dmg-check"
rm -rf "$MOUNT"
mkdir -p "$MOUNT"
hdiutil_retry attach attach -nobrowse -readonly -mountpoint "$MOUNT" "$DMG" >/dev/null
if ! codesign --verify --strict --deep --verbose=2 "$MOUNT/$APP_NAME.app"; then
  hdiutil_retry detach detach "$MOUNT" >/dev/null || true
  exit 1
fi
hdiutil_retry detach detach "$MOUNT" >/dev/null
if [[ "$NOTARIZE" = 1 ]]; then
  notarize "$DMG"
  stapler_retry staple "$DMG"
  stapler_retry validate "$DMG"
  spctl --assess --type open --context context:primary-signature -vvv "$DMG"
fi

echo "==> done"
ls -lh "$DMG"
