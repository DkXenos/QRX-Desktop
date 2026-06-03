#!/usr/bin/env bash
# build.sh — Build QRX-Desktop as a macOS .app using PyInstaller
# Usage: chmod +x build.sh && ./build.sh
set -euo pipefail

APP_NAME="QRX-Desktop"
ENTRY="main.py"
ICON="assets/icon.icns"

echo ""
echo "============================================"
echo "  Building $APP_NAME for macOS"
echo "============================================"
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Install dependencies
echo "[1/2] Installing dependencies ..."
pip install -r requirements.txt

# Run PyInstaller
echo "[2/2] Running PyInstaller ..."
if [ -f "$ICON" ]; then
    pyinstaller \
        --noconfirm \
        --windowed \
        --name "$APP_NAME" \
        --icon "$ICON" \
        "$ENTRY"
else
    pyinstaller \
        --noconfirm \
        --windowed \
        --name "$APP_NAME" \
        "$ENTRY"
fi

echo ""
echo "============================================"
echo "  ✅ Build complete!"
echo "  Output: dist/$APP_NAME.app"
echo "============================================"
