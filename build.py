"""Build QRX Desktop into an app your friends can double-click (no Python needed).

    python build.py

The same command works everywhere and builds for the computer it runs on:
dist/QRX-Desktop.exe on Windows, dist/QRX-Desktop.app on macOS and
dist/QRX-Desktop on Linux. No computer can build apps for the other systems,
so GitHub Actions runs this script on Windows and macOS to make each release.
"""

import subprocess
import sys
from pathlib import Path

APP = "QRX-Desktop"
ROOT = Path(__file__).resolve().parent


def run(*command):
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    # Use the project's .venv when there is one, like the old build.sh did.
    venv = ROOT / ".venv"
    venv_python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if venv_python.exists() and Path(sys.prefix).resolve() != venv.resolve():
        sys.exit(subprocess.call([str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]]))

    run(sys.executable, "-m", "pip", "install", "--quiet", "-r", "requirements.txt", "pyinstaller>=6")
    run(sys.executable, "-m", "unittest", "--quiet")  # never ship a build that fails its tests

    options = ["--noconfirm", "--clean", "--windowed", "--noupx", "--name", APP]
    # A Mac .app is already a single thing to share; elsewhere pack everything into one file.
    options.append("--onedir" if sys.platform == "darwin" else "--onefile")
    native_icon = {"win32": "icon.ico", "darwin": "icon.icns"}.get(sys.platform, "icon.png")
    for icon in (ROOT / "assets" / native_icon, ROOT / "assets" / "icon.png"):
        if icon.exists():  # PyInstaller converts a .png icon itself
            options += ["--icon", str(icon)]
            break
    run(sys.executable, "-m", "PyInstaller", *options, "main.py")

    built = {"win32": f"{APP}.exe", "darwin": f"{APP}.app"}.get(sys.platform, APP)
    print(f"\nBuild complete: {ROOT / 'dist' / built}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"\nBuild failed: `{' '.join(exc.cmd)}` exited with code {exc.returncode}.")
