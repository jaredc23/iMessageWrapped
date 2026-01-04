#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 path/to/source-image.png"
  exit 1
fi
SRC="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC="$ROOT/public"
TAURI_ICONS="$ROOT/src-tauri/icons"
mkdir -p "$PUBLIC" "$TAURI_ICONS"

if command -v magick >/dev/null 2>&1; then
  echo "Using ImageMagick (magick)"
  magick "$SRC" -resize 192x192^ -gravity center -extent 192x192 "$PUBLIC/logo192.png"
  magick "$SRC" -resize 512x512^ -gravity center -extent 512x512 "$PUBLIC/logo512.png"
  magick "$SRC" -resize 64x64 "$PUBLIC/favicon.ico"
  magick "$SRC" -resize 512x512 "$TAURI_ICONS/icon.png"
elif command -v convert >/dev/null 2>&1; then
  echo "Using ImageMagick (convert)"
  convert "$SRC" -resize 192x192^ -gravity center -extent 192x192 "$PUBLIC/logo192.png"
  convert "$SRC" -resize 512x512^ -gravity center -extent 512x512 "$PUBLIC/logo512.png"
  convert "$SRC" -resize 64x64 "$PUBLIC/favicon.ico"
  convert "$SRC" -resize 512x512 "$TAURI_ICONS/icon.png"
else
  echo "ImageMagick not found; using sips for PNGs (no .ico generation)"
  sips -Z 192 "$SRC" --out "$PUBLIC/logo192.png"
  sips -Z 512 "$SRC" --out "$PUBLIC/logo512.png"
  sips -Z 512 "$SRC" --out "$TAURI_ICONS/icon.png"
  echo "favicon.ico not generated; install ImageMagick for .ico support."
fi

# Create .icns for macOS apps using iconutil
ICONSET_DIR="$(mktemp -d)/icon.iconset"
mkdir -p "$ICONSET_DIR"
sips -Z 16 "$SRC" --out "$ICONSET_DIR/icon_16x16.png"
sips -Z 32 "$SRC" --out "$ICONSET_DIR/icon_32x32.png"
sips -Z 64 "$SRC" --out "$ICONSET_DIR/icon_64x64.png"
sips -Z 128 "$SRC" --out "$ICONSET_DIR/icon_128x128.png"
sips -Z 256 "$SRC" --out "$ICONSET_DIR/icon_256x256.png"
sips -Z 512 "$SRC" --out "$ICONSET_DIR/icon_512x512.png"
# 2x versions
sips -Z 32 "$SRC" --out "$ICONSET_DIR/icon_16x16@2x.png"
sips -Z 64 "$SRC" --out "$ICONSET_DIR/icon_32x32@2x.png"
sips -Z 128 "$SRC" --out "$ICONSET_DIR/icon_64x64@2x.png"
sips -Z 256 "$SRC" --out "$ICONSET_DIR/icon_128x128@2x.png"
sips -Z 512 "$SRC" --out "$ICONSET_DIR/icon_256x256@2x.png"
sips -Z 1024 "$SRC" --out "$ICONSET_DIR/icon_512x512@2x.png"

ICON_ICNS="$TAURI_ICONS/icon.icns"
if command -v iconutil >/dev/null 2>&1; then
  iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"
  echo "Generated $ICON_ICNS"
else
  echo "iconutil not found; cannot create .icns file."
fi

# Ensure there's at least a 512 PNG for Tauri
cp -f "$SRC" "$TAURI_ICONS/icon.png" || true

echo "Generated files (if available):"
ls -l "$PUBLIC/logo192.png" "$PUBLIC/logo512.png" "$PUBLIC/favicon.ico" "$TAURI_ICONS/icon.png" "$ICON_ICNS" 2>/dev/null || true
echo "Done."
