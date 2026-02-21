# QRX-Desktop

A cross-platform desktop GUI app for generating QR codes from URLs. Built with Python and Tkinter — no terminal needed.

---

## Features

- Simple, clean GUI window
- Enter any URL/link and an output filename
- QR code is saved as a `.jpg` directly to your Desktop
- Success and error messages shown in the app (no terminal)
- Works on macOS and Windows

---

## For Users (No Python Required)

Download the latest release for your platform from the [Releases page](../../releases):

| Platform | File |
|----------|------|
| macOS    | `QRX-Desktop-mac.zip` → extract and run `QRX-Desktop.app` |
| Windows  | `QRX-Desktop.exe` → double-click to run |

> On macOS, if you see a security warning, right-click the `.app` → Open → Open anyway.

---

## For Developers

### Prerequisites

- Python 3.12
- `pip`

### Setup

```bash
# Clone the repo
git clone https://github.com/jaysn/QRX-Desktop.git
cd QRX-Desktop

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate.bat     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the App

```bash
python main.py
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `qrcode[pil]` | QR code generation |
| `Pillow` | Image rendering and saving |
| `pyinstaller` | Packaging into standalone executables |

> Tkinter is built into Python — no separate install needed.

---

## Building a Standalone Executable

> ⚠️ PyInstaller can only build for the OS it's run on.

### macOS

```bash
chmod +x build.sh
./build.sh
```

Output: `dist/QRX-Desktop.app`

### Windows

```bat
build.bat
```

Output: `dist\QRX-Desktop.exe`

---

## Automated Cross-Platform Builds (GitHub Actions)

Push a version tag to trigger automatic builds for both macOS and Windows:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow (`.github/workflows/build.yml`) will:
1. Build `QRX-Desktop.app` on a macOS runner
2. Build `QRX-Desktop.exe` on a Windows runner
3. Attach both to a GitHub Release automatically

---

## Project Structure

```
QRX-Desktop/
├── .github/
│   └── workflows/
│       └── build.yml       # CI/CD: cross-platform builds
├── assets/
│   └── icon.png            # App icon (optional)
├── main.py                 # Main GUI app (Tkinter)
├── requirements.txt        # Python dependencies
├── build.sh                # macOS build script
├── build.bat               # Windows build script
└── README.md               # This file
```

---

## Developer

**jaysn** — based on the original [QRX CLI tool](../QRX)
# QRX-Deskop
