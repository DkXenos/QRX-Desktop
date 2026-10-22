# QRX-Desktop

Turn any link into a QR code image. QRX Desktop is one small Python script ([main.py](main.py)) that runs the same way on Windows, macOS and Linux.

1. Paste a link.
2. Type a file name.
3. Click **Generate QR Code** (or press Enter).

The image is saved as a `.jpg` on your **Desktop**. On Windows that is wherever your Desktop really is, including one that OneDrive backup moved (for example `OneDrive - Universitas Ciputra\Desktop`). Click **Change…** to save somewhere else.

---

## Download (no Python needed)

Get the files from the latest [release](../../releases/latest):

| Computer | File | First launch |
|----------|------|--------------|
| Windows 10/11 | `QRX-Desktop.exe` | Double-click it. If you see "Windows protected your PC", click **More info → Run anyway**. |
| Mac (Apple silicon) | `QRX-Desktop-mac.zip` | Unzip it and open `QRX-Desktop.app`. If macOS blocks it, open **System Settings → Privacy & Security** and click **Open Anyway**. |

On an Intel Mac or on Linux, run it from source (below).

---

## Run from source (any OS)

Needs Python 3.9 or newer.

```bash
pip install -r requirements.txt
python main.py
```

On Linux you may also need Tkinter: `sudo apt install python3-tk`.

## Test

```bash
pip install zxing-cpp   # optional: lets the tests scan the QR images they make
python -m unittest -v
```

The tests cover a Desktop that OneDrive moved or renamed, PCs with no Desktop at all, Linux desktops in other languages, file names Windows rejects, folders you can't write to, and the window itself.

## Build the double-click app

```bash
python build.py
```

It's one command on every OS. It installs what it needs, runs the tests, and builds the app for the computer it runs on: `dist/QRX-Desktop.exe` on Windows, `dist/QRX-Desktop.app` on macOS. No computer can build apps for the other operating systems, so GitHub Actions builds both for you.

## Release

```bash
git tag v2.1.0
git push origin v2.1.0
```

[GitHub Actions](.github/workflows/build.yml) runs the tests on Windows, macOS and Linux, runs `build.py` on Windows and macOS, checks that each app opens, and attaches `QRX-Desktop.exe` and `QRX-Desktop-mac.zip` to a new release. Every other push runs the same tests and builds without releasing.

---

## Project Structure

```
QRX-Desktop/
├── main.py                  # The app
├── test_main.py             # Tests
├── build.py                 # Builds the double-click app (any OS)
├── requirements.txt         # Python packages the app needs
├── assets/icon.png          # Optional app icon (icon.ico / icon.icns also work)
└── .github/workflows/
    └── build.yml            # Tests, builds and releases on GitHub
```

---

## Developer

**jaysn** — based on the original [QRX CLI tool](../QRX)
