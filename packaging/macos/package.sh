#!/usr/bin/env bash
# build_dmg.sh: builds "Court binder builder.app" and a drag-to-Applications .dmg.
#
# Usage (from anywhere):   packaging/macos/build_dmg.sh
#
# It creates its own build environment (packaging/macos/.venv-build) so nothing is
# installed into app/.venv. Needs Python 3.10+ and, for the bundled PdfCraft engine,
# the same Python version and processor type as the pdfcraft wheel (see below).
#
# PdfCraft native engine (optional, on by default). The installer does what
#   pip install "<wheel url>"
# does, at build time, so users never run pip:
#   PDFCRAFT_WHEEL_URL     wheel to download (default: the v0.16.1 release, Python 3.13, Apple Silicon)
#   PDFCRAFT_WHEEL_SHA256  expected SHA-256 of that wheel (default: the pinned release hash)
#   PDFCRAFT_WHEEL         use a local wheel file instead (for example one built in ../pdfcraft);
#                          its hash is checked only if PDFCRAFT_WHEEL_SHA256 is also set
#   WITH_PDFCRAFT=0        build without it
#   BUILD_PYTHON           Python to create the build environment with (default python3)
#
# Optional signing and notarization (needs an Apple Developer account; untested here):
#   SIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"   signs the app
#   NOTARY_PROFILE="my-notary-profile"                              notarizes and staples the .dmg
#       (create the profile once: xcrun notarytool store-credentials my-notary-profile)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
VENV="${BUILD_VENV:-$HERE/.venv-build}"
APP_NAME="Court binder builder"
WITH_PDFCRAFT="${WITH_PDFCRAFT:-1}"
PDFCRAFT_WHEEL_URL="${PDFCRAFT_WHEEL_URL:-https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl}"
PDFCRAFT_DEFAULT_SHA256="53f52d2f154d723c50836c2820f9ce19fb4bc9f0c2bd88c48f1b8e3b2a364f46"

cd "$HERE"
rm -rf build dist

echo "==> Preparing the build environment ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  "${BUILD_PYTHON:-python3}" -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q -r "$ROOT/app/requirements-build.txt"

if [ "$WITH_PDFCRAFT" = "1" ]; then
  mkdir -p build/wheel
  if [ -n "${PDFCRAFT_WHEEL:-}" ]; then
    WHEEL="$PDFCRAFT_WHEEL"
    EXPECTED="${PDFCRAFT_WHEEL_SHA256:-}"
    echo "==> Using local PdfCraft wheel: $WHEEL"
  else
    WHEEL="build/wheel/$(basename "$PDFCRAFT_WHEEL_URL")"
    EXPECTED="${PDFCRAFT_WHEEL_SHA256:-$PDFCRAFT_DEFAULT_SHA256}"
    echo "==> Downloading the PdfCraft wheel"
    curl -fL --silent --show-error -o "$WHEEL" "$PDFCRAFT_WHEEL_URL"
  fi
  if [ -n "$EXPECTED" ]; then
    ACTUAL="$(shasum -a 256 "$WHEEL" | awk '{print $1}')"
    if [ "$ACTUAL" != "$EXPECTED" ]; then
      echo "PdfCraft wheel hash mismatch: expected $EXPECTED, got $ACTUAL. Refusing to bundle it." >&2
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

VERSION="$("$VENV/bin/python" -c "import sys; sys.path.insert(0, '$ROOT/app'); import binder_app; print(binder_app.__version__)")"
ARCH="$(uname -m)"

echo "==> Building $APP_NAME.app ($VERSION, $ARCH)"
"$VENV/bin/pyinstaller" --noconfirm --clean --distpath dist --workpath build binder_app.spec

APP="dist/$APP_NAME.app"

if [ -n "${SIGN_IDENTITY:-}" ]; then
  echo "==> Signing with $SIGN_IDENTITY"
  codesign --force --deep --options runtime --timestamp --sign "$SIGN_IDENTITY" "$APP"
else
  echo "==> No SIGN_IDENTITY set: the app is ad-hoc signed only (fine to run on this Mac)"
  codesign --force --deep --sign - "$APP"
fi

echo "==> Self-test of the packaged app (no window)"
SELFTEST_ARGS=(--selftest)
[ "$WITH_PDFCRAFT" = "1" ] && SELFTEST_ARGS+=(--require-pdfcraft)
"$APP/Contents/MacOS/$APP_NAME" "${SELFTEST_ARGS[@]}"

echo "==> Creating the .dmg"
STAGE="dist/dmg"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
DMG="dist/Court-binder-builder-$VERSION-macos-$ARCH.dmg"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null

if [ -n "${SIGN_IDENTITY:-}" ] && [ -n "${NOTARY_PROFILE:-}" ]; then
  echo "==> Notarizing (this can take a few minutes)"
  codesign --force --sign "$SIGN_IDENTITY" "$DMG"
  xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait
  xcrun stapler staple "$DMG"
fi

echo "==> Done: $HERE/$DMG"
ls -lh "$DMG"
