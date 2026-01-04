#!/usr/bin/env bash
# Build a single-file native executable of Backend/MessagesWrapped.py using PyInstaller
# Places the produced binary into src-tauri/binaries/

set -euo pipefail

OUT_DIR="src-tauri/binaries"
mkdir -p "$OUT_DIR"

echo "Creating Python venv..."
python3 -m venv .pyvenv || true
source .pyvenv/bin/activate

echo "Installing pyinstaller..."
pip install --upgrade pip
pip install pyinstaller

SCRIPT_PATH="../Backend/MessagesWrapped.py"
echo "Building ${SCRIPT_PATH} (onefile)..."
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "Error: script file '$SCRIPT_PATH' does not exist. Make sure you run this from the 'messages-tauri-starter' folder where '../Backend/MessagesWrapped.py' is reachable." >&2
  exit 2
fi

pyinstaller --onefile --name MessagesWrapped "$SCRIPT_PATH"

PKG_BINARY="dist/MessagesWrapped"
if [ ! -f "$PKG_BINARY" ]; then
  # On Windows pyinstaller produces .exe
  if [ -f "dist/MessagesWrapped.exe" ]; then
    PKG_BINARY="dist/MessagesWrapped.exe"
  else
    echo "Build failed: no binary found in dist/" >&2
    exit 2
  fi
fi

echo "Copying binary to $OUT_DIR"
cp "$PKG_BINARY" "$OUT_DIR/"
chmod +x "$OUT_DIR/MessagesWrapped" || true

echo "Cleaning build artifacts..."
rm -rf build dist __pycache__ *.spec

echo "Done. Binary at $OUT_DIR/$(basename $PKG_BINARY)"
