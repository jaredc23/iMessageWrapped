#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT/venv"
TMP_REQS="$(mktemp)"
CURRENT_PY="${PYTHON:-python3}"

echo "Saving current environment packages to $TMP_REQS..."
"$CURRENT_PY" -m pip freeze > "$TMP_REQS"

if [ -d "$VENV_DIR" ]; then
  echo "Using existing venv at $VENV_DIR"
else
  echo "Creating venv at $VENV_DIR"
  "$CURRENT_PY" -m venv "$VENV_DIR"
fi

# Activate venv
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Upgrading pip and installing build tools..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install pyinstaller || true

echo "Installing packages from current environment into new venv (may fail for system-only packages)..."
python -m pip install -r "$TMP_REQS" || echo "Warning: some packages failed to install; continuing."

echo "Building executables from Backend/ using venv's Python..."
cd "$ROOT/Backend"

SCRIPTS=("iPhoneBackup.py" "MessageParser.py" "MessagesWrapped.py")
for s in "${SCRIPTS[@]}"; do
  name="${s%.py}"
  echo "Building $s -> $name"
  "$VENV_DIR/bin/python3" -m PyInstaller --onefile --clean --name "$name" "$s"
done

echo "Copying built executables to release folder (overwriting)..."
DEST1="$ROOT/Release/1.0"
DEST2="$ROOT/Release 1.0"
if [ -d "$DEST1" ]; then
  DEST="$DEST1"
elif [ -d "$DEST2" ]; then
  DEST="$DEST2"
else
  mkdir -p "$DEST1"
  DEST="$DEST1"
fi

for name in iPhoneBackup MessageParser MessagesWrapped; do
  src="$ROOT/Backend/dist/$name"
  if [ -f "$src" ]; then
    cp -f "$src" "$DEST/$name"
    chmod +x "$DEST/$name"
    echo "Copied $src -> $DEST/$name"
  else
    echo "Warning: $src not found; build may have failed for $name"
  fi
done

echo "Cleanup: removing temporary requirements file $TMP_REQS"
rm -f "$TMP_REQS"

echo "Done. Built on $(uname -m) and copied executables to $DEST"
