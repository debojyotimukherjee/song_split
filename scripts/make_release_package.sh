#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-$(date +%Y%m%d-%H%M)}"
PACKAGE_NAME="Wannabe-Stem-${VERSION}"
DIST_DIR="$ROOT_DIR/dist"
STAGE_DIR="$DIST_DIR/$PACKAGE_NAME"
ZIP_PATH="$DIST_DIR/$PACKAGE_NAME.zip"
CHECKSUM_PATH="$ZIP_PATH.sha256"

rm -rf "$STAGE_DIR" "$ZIP_PATH" "$CHECKSUM_PATH"
mkdir -p "$STAGE_DIR" "$STAGE_DIR/data/inbox" "$STAGE_DIR/data/jobs" "$STAGE_DIR/data/models"

rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude ".env" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  --exclude ".pytest_cache" \
  --exclude ".DS_Store" \
  --exclude "dist" \
  --exclude "data/inbox/*" \
  --exclude "data/jobs/*" \
  --exclude "data/models/*" \
  "$ROOT_DIR/" "$STAGE_DIR/"

chmod +x "$STAGE_DIR/Start Wannabe Stem.command"
chmod +x "$STAGE_DIR/Stop Wannabe Stem.command"
chmod +x "$STAGE_DIR/scripts/make_release_package.sh"

(
  cd "$DIST_DIR"
  zip -qr "$ZIP_PATH" "$PACKAGE_NAME"
)

if command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "$ZIP_PATH" > "$CHECKSUM_PATH"
else
  sha256sum "$ZIP_PATH" > "$CHECKSUM_PATH"
fi

echo "$ZIP_PATH"
echo "$CHECKSUM_PATH"
