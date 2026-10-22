r"""QRX Desktop: turn a link into a QR code image.

One script for Windows, macOS and Linux. Images are saved to your Desktop
(wherever Windows or OneDrive has moved it) unless you pick another folder.

    pip install -r requirements.txt
    python main.py
"""

import os
import re
import sys
import tkinter as tk
import traceback
from tkinter import filedialog, font, messagebox

import qrcode
from qrcode.exceptions import DataOverflowError

APP_NAME = "QRX Desktop"

# Windows refuses these file names, whatever the extension.
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    port + n for port in ("COM", "LPT") for n in "0123456789¹²³"
}

# Fixed dark palette, so the app looks the same on every OS and theme.
BG = "#1c1c1e"
SURFACE = "#3a3a3c"
BUTTON = "#48484a"
BUTTON_HOVER = "#5a5a5e"
ACCENT = "#0a84ff"
ACCENT_HOVER = "#0060df"
TEXT = "#f2f2f7"
MUTED = "#aeaeb2"


# ── Where to save ──────────────────────────────────────

def desktop_folder():
    """The default save folder: the Desktop, or the home folder if there is none."""
    home = os.path.expanduser("~")
    folders = [os.path.join(home, "Desktop")]
    try:
        if sys.platform == "win32":
            folders.insert(0, windows_desktop())
        elif sys.platform != "darwin":
            folders.insert(0, linux_desktop())
    except Exception:  # an unusual setup must never stop the app from opening
        pass
    for folder in folders:
        if folder and os.path.isdir(folder):
            return folder
    return home


def windows_desktop():
    r"""Ask Windows where the Desktop is.

    OneDrive backup, school or work accounts and language settings can move
    or rename it (e.g. C:\Users\Ana\OneDrive - Universitas Ciputra\Desktop),
    so ~\Desktop often doesn't exist. This is the official way to find it.
    """
    import ctypes
    import uuid

    folder_id = uuid.UUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641")  # FOLDERID_Desktop
    guid = (ctypes.c_ubyte * 16).from_buffer_copy(folder_id.bytes_le)
    path = ctypes.c_wchar_p()
    ctypes.oledll.shell32.SHGetKnownFolderPath(
        ctypes.byref(guid), 0, None, ctypes.byref(path)
    )
    try:
        return path.value
    finally:
        ctypes.windll.ole32.CoTaskMemFree(path)


def linux_desktop():
    """Read the Desktop from ~/.config/user-dirs.dirs; it may be renamed, e.g. "Schreibtisch"."""
    config = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    try:
        with open(os.path.join(config, "user-dirs.dirs"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("XDG_DESKTOP_DIR="):
                    return os.path.expandvars(line.split("=", 1)[1].strip().strip('"'))
    except OSError:
        pass
    return None


def clean_filename(name):
    """Turn what the user typed into a file name every OS accepts, ending in .jpg."""
    name = name.strip()
    if name.lower().endswith((".jpg", ".jpeg")):
        name = name.rsplit(".", 1)[0]
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if name.split(".")[0].upper() in WINDOWS_RESERVED:
        name = "_" + name
    return (name or "qr-code") + ".jpg"


def save_qr(link, path):
    """Draw the QR code for `link` and save it as a JPEG image at `path`."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(link)
    try:
        qr.make(fit=True)
    except ValueError:  # qrcode 8 reports "too much data" as "Invalid version (was 41...)"
        raise DataOverflowError() from None
    qr.make_image().convert("RGB").save(path, "JPEG", quality=95)


# ── Window ─────────────────────────────────────────────

class QRXApp:
    """A link box, a file name box, a Save-to folder and a Generate button."""

    def __init__(self, root):
        self.root = root
        self.family = font.nametofont("TkDefaultFont").actual("family")
        self.link = tk.StringVar()
        self.name = tk.StringVar()
        self.folder = tk.StringVar(value=desktop_folder())

        root.title(f"{APP_NAME} — QR Code Generator")
        root.configure(bg=BG, padx="20p", pady="14p")
        root.columnconfigure(0, weight=1)
        root.resizable(True, False)
        root.report_callback_exception = self.unexpected_error

        # Each grid() call without a row goes on the next row down.
        tk.Label(root, text=APP_NAME, font=(self.family, 22, "bold"),
                 bg=BG, fg=ACCENT).grid(pady=("10p", "2p"))
        tk.Label(root, text="Turn any link into a QR code", font=(self.family, 11),
                 bg=BG, fg=MUTED).grid(pady=(0, "10p"))

        self.label("Link")
        self.link_entry = self.entry(root, self.link)
        self.link_entry.grid(sticky="ew", ipady="5p")

        self.label("File name (saved as .jpg)")
        self.name_entry = self.entry(root, self.name)
        self.name_entry.grid(sticky="ew", ipady="5p")

        self.label("Save to")
        row = tk.Frame(root, bg=BG)
        row.grid(sticky="ew")
        row.columnconfigure(0, weight=1)
        self.folder_entry = self.entry(row, self.folder, width=28)
        self.folder_entry.grid(row=0, column=0, sticky="ew", ipady="5p")
        # Long paths: keep the end visible ("...\OneDrive - School\Desktop").
        self.folder_entry.bind("<Configure>", lambda event: self.folder_entry.xview_moveto(1))
        self.change_button = self.button(row, "Change…", self.choose_folder,
                                         BUTTON, BUTTON_HOVER, size=11, padx="10p")
        self.change_button.grid(row=0, column=1, sticky="ns", padx=("6p", 0))

        self.generate_button = self.button(root, "Generate QR Code", self.generate,
                                           ACCENT, ACCENT_HOVER, size=13, padx="26p", pady="9p")
        self.generate_button.grid(pady=("18p", "8p"))

        root.bind("<Return>", lambda event: self.generate())
        root.bind("<KP_Enter>", lambda event: self.generate())
        self.link_entry.focus_set()

    def label(self, text):
        tk.Label(self.root, text=text, font=(self.family, 12, "bold"),
                 bg=BG, fg=TEXT).grid(sticky="w", pady=("8p", "3p"))

    def entry(self, parent, variable, width=36):
        entry = tk.Entry(
            parent, textvariable=variable, width=width, font=(self.family, 13),
            relief="flat", bd=0, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            selectbackground=ACCENT, selectforeground=TEXT,
            highlightthickness=2, highlightbackground=SURFACE, highlightcolor=ACCENT,
        )
        # Right-click menu, because lots of people paste links that way.
        menu = tk.Menu(entry, tearoff=False)
        for action in ("Cut", "Copy", "Paste"):
            menu.add_command(label=action, command=lambda a=action: entry.event_generate(f"<<{a}>>"))
        right_clicks = ("<Button-2>", "<Button-3>") if sys.platform == "darwin" else ("<Button-3>",)
        for click in right_clicks:
            entry.bind(click, lambda event: menu.tk_popup(event.x_root, event.y_root))
        return entry

    def button(self, parent, text, command, color, hover, size, **padding):
        """A Label dressed as a button, because macOS ignores colours on tk.Button."""
        button = tk.Label(parent, text=text, font=(self.family, size, "bold"),
                          bg=color, fg=TEXT, cursor="hand2", **padding)
        button.bind("<Button-1>", lambda event: command())
        button.bind("<Enter>", lambda event: button.configure(bg=hover))
        button.bind("<Leave>", lambda event: button.configure(bg=color))
        return button

    def choose_folder(self):
        current = self.folder.get()
        chosen = filedialog.askdirectory(
            parent=self.root, title="Save QR codes in…", mustexist=True,
            initialdir=current if os.path.isdir(current) else os.path.expanduser("~"),
        )
        if chosen:  # empty when the user cancels
            self.folder.set(os.path.normpath(chosen))
            self.folder_entry.xview_moveto(1)

    def generate(self):
        link = self.link.get().strip()
        name = self.name.get().strip()
        folder = os.path.expanduser(self.folder.get().strip())

        if not link:
            self.error("Paste or type a link first.")
            return
        if not name:
            self.error("Type a name for the image file.")
            return
        if not os.path.isdir(folder):
            self.error(f"This folder doesn't exist:\n{folder}\n\n"
                       "Click “Change…” to pick another one.")
            return

        path = os.path.join(folder, clean_filename(name))
        if os.path.exists(path) and not messagebox.askyesno(
            APP_NAME, f"“{os.path.basename(path)}” is already in this folder. Replace it?",
            parent=self.root,
        ):
            return
        try:
            save_qr(link, path)
        except DataOverflowError:
            self.error("That link is too long to fit in a QR code.")
            return
        except OSError as exc:  # e.g. no permission, or Windows' "Controlled folder access"
            self.error(f"Couldn't save in:\n{folder}\n\n{exc.strerror or exc}\n\n"
                       "Click “Change…” to pick another folder.")
            return

        messagebox.showinfo(APP_NAME, f"QR code saved!\n\n{path}", parent=self.root)
        self.link.set("")
        self.name.set("")
        self.link_entry.focus_set()

    def error(self, message):
        messagebox.showerror(APP_NAME, message, parent=self.root)

    def unexpected_error(self, exc_type, exc, tb):
        """Show surprises in a dialog: a double-clicked app has no terminal to print to."""
        if sys.stderr:  # None in a double-clicked Windows app
            traceback.print_exception(exc_type, exc, tb)
        self.error(f"Something went wrong:\n{exc}")


def main():
    if sys.platform == "win32":
        try:  # sharp text on high-DPI laptops instead of a blurry, stretched window
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    if sys.platform != "darwin":
        # Sizes are in points. Make 1pt = 1px on a normal screen and scale up on
        # high-DPI ones; macOS already handles Retina screens by itself.
        root.tk.call("tk", "scaling", max(1.0, root.winfo_fpixels("1i") / 96))
    QRXApp(root)
    root.update_idletasks()
    root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())
    root.eval("tk::PlaceWindow . center")
    root.mainloop()


if __name__ == "__main__":
    main()
