#!/usr/bin/env bash
# build.sh — Build QRX-Desktop as a macOS .app using PyInstaller
set -e

APP_NAME="QRX-Desktop"
ENTRY="main.py"
ICON="assets/icon.png"

echo "=== Building $APP_NAME for macOS ==="

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt

# Run PyInstaller
if [ -f "$ICON" ]; then
    pyinstaller \
        --onefile \
        --windowed \
        --name "$APP_NAME" \
        --icon "$ICON" \
        "$ENTRY"
else
    pyinstaller \
        --onefile \
        --windowed \
        --name "$APP_NAME" \
        "$ENTRY"
fi

echo ""
echo "✅ Build complete! Find your app in: dist/$APP_NAME.app"
