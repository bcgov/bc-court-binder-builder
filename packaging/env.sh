# shellcheck shell=bash
# Shared setup for the packaging scripts, adapted from the PdfCraft packaging
# (https://github.com/richfrem/pdfcraft, packaging/env.sh). Source it:
#   . "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
#
# Exports:
#   ROOT     repository root
#   VERSION  the app version, read from app/binder_app/__init__.py (override: CBB_VERSION)
#   DIST     output directory for release artifacts (default: $ROOT/dist/release)
# Defines: warn

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROOT

# The version lives in exactly one place: __version__ in app/binder_app/__init__.py.
app_version() {
  sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$ROOT/app/binder_app/__init__.py" | head -n 1
}

VERSION="${CBB_VERSION:-$(app_version)}"
if [[ -z "$VERSION" ]]; then
  echo "error: could not read __version__ from $ROOT/app/binder_app/__init__.py" >&2
  exit 1
fi
case "$VERSION" in
  *[!A-Za-z0-9.-]* | .* | *.)
    echo "error: VERSION may hold only letters, digits, dots and dashes: $VERSION" >&2
    exit 1
    ;;
  *) ;;
esac
export VERSION

DIST="${DIST:-$ROOT/dist/release}"
mkdir -p "$DIST"
export DIST

# A warning that GitHub Actions shows on the run page; plain text elsewhere.
warn() {
  if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
    echo "::warning::$*"
  else
    echo "warning: $*" >&2
  fi
}
