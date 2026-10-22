"""Tests for main.py. Run them with:  python -m unittest -v

They cover what broke on friends' laptops (a Desktop that Windows moved into
OneDrive, renamed, or doesn't have), file names Windows rejects, folders that
can't be written to, and the window itself. On Windows they also check the
real Desktop lookup; on other systems it is simulated.
"""

import os
import subprocess
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

import main

try:
    import zxingcpp  # optional: scans the saved images like a phone camera would
except ImportError:
    zxingcpp = None

HERE = Path(__file__).resolve().parent


class FakeHomeTestCase(unittest.TestCase):
    """Each test gets an empty home folder whose name has accents and spaces."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name, "Jöse Ñandú 李")
        self.home.mkdir()
        env = mock.patch.dict(os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("XDG_CONFIG_HOME", None)

    def folder(self, *parts):
        path = self.home.joinpath(*parts)
        path.mkdir(parents=True)
        return str(path)

    def pretend(self, platform):
        patcher = mock.patch.object(sys, "platform", platform)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assertSamePath(self, actual, expected):
        self.assertEqual(os.path.normcase(os.path.normpath(actual)),
                         os.path.normcase(os.path.normpath(expected)))


class DesktopFolderTests(FakeHomeTestCase):
    def test_macos(self):
        self.pretend("darwin")
        desktop = self.folder("Desktop")
        self.assertSamePath(main.desktop_folder(), desktop)

    def test_windows_desktop_moved_into_onedrive(self):
        # v1.0.0 only looked at ~\Desktop, which OneDrive backup moves away.
        self.pretend("win32")
        desktop = self.folder("OneDrive", "Desktop")
        with mock.patch.object(main, "windows_desktop", return_value=desktop):
            self.assertSamePath(main.desktop_folder(), desktop)

    def test_windows_school_account_onedrive(self):
        # School and work accounts use "OneDrive - <name>", which v2.0.0 never checked.
        self.pretend("win32")
        desktop = self.folder("OneDrive - Universitas Ciputra", "Desktop")
        with mock.patch.object(main, "windows_desktop", return_value=desktop):
            self.assertSamePath(main.desktop_folder(), desktop)

    def test_windows_renamed_desktop(self):
        # Some languages rename the folder itself, e.g. Spanish OneDrive uses "Escritorio".
        self.pretend("win32")
        desktop = self.folder("OneDrive", "Escritorio")
        with mock.patch.object(main, "windows_desktop", return_value=desktop):
            self.assertSamePath(main.desktop_folder(), desktop)

    def test_windows_lookup_fails(self):
        self.pretend("win32")
        desktop = self.folder("Desktop")
        with mock.patch.object(main, "windows_desktop", side_effect=OSError("shell32 failed")):
            self.assertSamePath(main.desktop_folder(), desktop)

    def test_windows_lookup_points_at_missing_folder(self):
        self.pretend("win32")
        desktop = self.folder("Desktop")
        unplugged = str(self.home / "unplugged drive" / "Desktop")
        with mock.patch.object(main, "windows_desktop", return_value=unplugged):
            self.assertSamePath(main.desktop_folder(), desktop)

    def test_no_desktop_anywhere_uses_home(self):
        for platform in ("win32", "darwin", "linux"):
            with self.subTest(platform=platform), mock.patch.object(sys, "platform", platform), \
                    mock.patch.object(main, "windows_desktop", return_value=None):
                self.assertSamePath(main.desktop_folder(), self.home)

    def test_linux_renamed_desktop(self):
        self.pretend("linux")
        desktop = self.folder("Schreibtisch")
        Path(self.folder(".config"), "user-dirs.dirs").write_text(
            '# written by xdg-user-dirs-update\nXDG_DESKTOP_DIR="$HOME/Schreibtisch"\n',
            encoding="utf-8")
        self.assertSamePath(main.desktop_folder(), desktop)

    def test_linux_custom_config_folder(self):
        self.pretend("linux")
        desktop = self.folder("Área de Trabalho")
        config = self.folder("my config")
        Path(config, "user-dirs.dirs").write_text(f'XDG_DESKTOP_DIR="{desktop}"\n', encoding="utf-8")
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": config}):
            self.assertSamePath(main.desktop_folder(), desktop)

    def test_linux_without_config(self):
        self.pretend("linux")
        desktop = self.folder("Desktop")
        self.assertSamePath(main.desktop_folder(), desktop)


@unittest.skipUnless(sys.platform == "win32", "needs Windows")
class RealWindowsTests(unittest.TestCase):
    def test_same_answer_as_windows_itself(self):
        # .NET asks the same Windows API, so the two must agree.
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "[Console]::OutputEncoding = [Text.Encoding]::UTF8; [Environment]::GetFolderPath('Desktop')"],
            capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(os.path.normcase(main.windows_desktop()),
                         os.path.normcase(result.stdout.strip()))
        self.assertTrue(os.path.isdir(main.desktop_folder()))

    @unittest.skipUnless(os.environ.get("QRX_TEST_MOVE_DESKTOP") == "1",
                         "briefly moves this PC's Desktop setting; set QRX_TEST_MOVE_DESKTOP=1 (CI does)")
    def test_follows_desktop_moved_into_school_onedrive(self):
        # Do what OneDrive backup does on a school account, then look the Desktop up fresh.
        import winreg

        moved = r"%USERPROFILE%\OneDrive - Universitas Ciputra\Desktop"
        os.makedirs(os.path.expandvars(moved), exist_ok=True)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
        original, kind = winreg.QueryValueEx(key, "Desktop")
        winreg.SetValueEx(key, "Desktop", 0, winreg.REG_EXPAND_SZ, moved)
        try:
            found = subprocess.run(
                [sys.executable, "-c", "import main; print(main.desktop_folder())"],
                cwd=HERE, capture_output=True, text=True, encoding="utf-8", check=True,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}).stdout.strip()
        finally:
            winreg.SetValueEx(key, "Desktop", 0, kind, original)
            winreg.CloseKey(key)
        self.assertEqual(os.path.normcase(found), os.path.normcase(os.path.expandvars(moved)))


class CleanFilenameTests(unittest.TestCase):
    CASES = {
        "my qr": "my qr.jpg",
        "promo.JPG": "promo.jpg",
        "photo.jpeg": "photo.jpg",
        "QR: promo?": "QR_ promo_.jpg",
        "a/b\\c": "a_b_c.jpg",
        'say "hi" <now>|*': "say _hi_ _now___.jpg",
        "tab\there": "tab_here.jpg",
        "name. ": "name.jpg",
        ".hidden": "hidden.jpg",
        "...": "qr-code.jpg",
        "CON": "_CON.jpg",
        "nul.jpg": "_nul.jpg",
        "com1.txt": "_com1.txt.jpg",
        "console": "console.jpg",
        "kopi ☕ 二维码": "kopi ☕ 二维码.jpg",
    }

    def test_cleaning(self):
        for typed, expected in self.CASES.items():
            with self.subTest(typed=typed):
                self.assertEqual(main.clean_filename(typed), expected)

    def test_cleaned_names_work_on_this_computer(self):
        # The real check: this OS can create every cleaned name, unchanged.
        with tempfile.TemporaryDirectory() as tmp:
            for typed in self.CASES:
                with self.subTest(typed=typed):
                    name = main.clean_filename(typed)
                    Path(tmp, name).write_bytes(b"ok")
                    self.assertIn(name, os.listdir(tmp))


class SaveQRTests(FakeHomeTestCase):
    def test_saves_a_jpeg(self):
        path = str(self.home / "qr.jpg")
        main.save_qr("https://uc.ac.id", path)
        with Image.open(path) as image:
            self.assertEqual((image.format, image.mode), ("JPEG", "RGB"))
            self.assertGreater(image.width, 200)

    @unittest.skipIf(zxingcpp is None, "pip install zxing-cpp to scan the images too")
    def test_images_scan_back_to_the_link(self):
        links = [
            "https://uc.ac.id",
            "https://例子.测试/路径?q=kopi ☕",
            "WIFI:S:Kos Ana;T:WPA;P:rahasia123;;",
            "https://example.com/" + "x" * 1100,  # close to the most a QR code can hold
        ]
        for i, link in enumerate(links):
            with self.subTest(link=link[:30]):
                path = str(self.home / f"qr {i}.jpg")
                main.save_qr(link, path)
                with Image.open(path) as image:
                    self.assertEqual([code.text for code in zxingcpp.read_barcodes(image)], [link])

    def test_link_too_long_for_a_qr_code(self):
        with self.assertRaises(main.DataOverflowError):
            main.save_qr("https://example.com/" + "x" * 3000, str(self.home / "qr.jpg"))


class AppTests(FakeHomeTestCase):
    """Drives the real window, with pop-up dialogs replaced by mocks."""

    def setUp(self):
        super().setUp()
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            if os.environ.get("CI"):  # CI machines have a (virtual) screen: a failure here is real
                raise
            self.skipTest(f"no display: {exc}")
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.desktop = self.folder("Desktop")
        with mock.patch.object(main, "desktop_folder", return_value=self.desktop):
            self.app = main.QRXApp(self.root)
        self.dialogs = {}
        for name in ("showinfo", "showerror", "askyesno"):
            patcher = mock.patch.object(main.messagebox, name, return_value=True)
            self.dialogs[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def fill(self, link="https://uc.ac.id", name="my qr"):
        self.app.link.set(link)
        self.app.name.set(name)

    def last_error(self):
        return self.dialogs["showerror"].call_args[0][1]

    def test_starts_on_the_desktop(self):
        self.assertEqual(self.app.folder.get(), self.desktop)

    def test_generate_saves_to_the_desktop(self):
        self.fill()
        self.app.generate()
        self.assertTrue(Path(self.desktop, "my qr.jpg").is_file())
        self.dialogs["showinfo"].assert_called_once()
        self.dialogs["showerror"].assert_not_called()
        self.assertEqual((self.app.link.get(), self.app.name.get()), ("", ""))

    def test_change_folder(self):
        other = self.folder("QR codes")
        with mock.patch.object(main.filedialog, "askdirectory", return_value=other):
            self.app.choose_folder()
        self.assertSamePath(self.app.folder.get(), other)
        self.fill()
        self.app.generate()
        self.assertTrue(Path(other, "my qr.jpg").is_file())
        self.assertEqual(os.listdir(self.desktop), [])

    def test_cancelling_change_keeps_the_folder(self):
        with mock.patch.object(main.filedialog, "askdirectory", return_value=""):
            self.app.choose_folder()
        self.assertEqual(self.app.folder.get(), self.desktop)

    def test_missing_link_or_name(self):
        for link, name in (("", "my qr"), ("https://uc.ac.id", ""), ("   ", "   ")):
            with self.subTest(link=link, name=name):
                self.dialogs["showerror"].reset_mock()
                self.fill(link, name)
                self.app.generate()
                self.dialogs["showerror"].assert_called_once()
        self.assertEqual(os.listdir(self.desktop), [])

    def test_folder_that_no_longer_exists(self):
        self.app.folder.set(str(self.home / "USB stick"))
        self.fill()
        self.app.generate()
        self.assertIn("doesn't exist", self.last_error())

    def test_asks_before_replacing_a_file(self):
        existing = Path(self.desktop, "my qr.jpg")
        existing.write_bytes(b"old")
        self.dialogs["askyesno"].return_value = False
        self.fill()
        self.app.generate()
        self.assertEqual(existing.read_bytes(), b"old")
        self.dialogs["askyesno"].return_value = True
        self.app.generate()
        self.assertNotEqual(existing.read_bytes(), b"old")

    def test_windows_unfriendly_name_still_saves(self):
        self.fill(name="QR: promo?")
        self.app.generate()
        self.assertTrue(Path(self.desktop, "QR_ promo_.jpg").is_file())

    def test_not_allowed_to_save_here(self):
        # e.g. Windows "Controlled folder access" blocking the Desktop
        self.fill()
        with mock.patch.object(main, "save_qr", side_effect=PermissionError(13, "Permission denied")):
            self.app.generate()
        self.assertIn("Permission denied", self.last_error())
        self.assertIn("Change", self.last_error())

    @unittest.skipIf(sys.platform == "win32" or os.geteuid() == 0, "needs a POSIX non-root user")
    def test_read_only_folder(self):
        locked = self.folder("locked")
        os.chmod(locked, 0o500)
        self.addCleanup(os.chmod, locked, 0o700)
        self.app.folder.set(locked)
        self.fill()
        self.app.generate()
        self.assertIn("Change", self.last_error())

    def test_link_too_long(self):
        self.fill(link="https://example.com/" + "x" * 3000)
        self.app.generate()
        self.assertIn("too long", self.last_error())

    def test_unexpected_errors_show_a_dialog(self):
        with mock.patch.object(sys, "stderr", None):  # like a double-clicked Windows app
            self.app.unexpected_error(ValueError, ValueError("boom"), None)
        self.assertIn("boom", self.last_error())

    def test_layout_stretches_sideways_and_enter_generates(self):
        wide, tall = (bool(int(flag)) for flag in self.root.tk.splitlist(self.root.resizable()))
        self.assertTrue(wide)
        if tk.TkVersion >= 8.6:  # Apple's old Tk 8.5 can't lock just the height
            self.assertFalse(tall)
        self.assertEqual(int(self.root.grid_columnconfigure(0)["weight"]), 1)
        for entry in (self.app.link_entry, self.app.name_entry):
            self.assertEqual(entry.grid_info()["sticky"], "ew")
        self.assertTrue(self.root.bind("<Return>"))


if __name__ == "__main__":
    unittest.main()
