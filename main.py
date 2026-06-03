import sys
import platform
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

import qrcode


def get_desktop_path() -> Path:
    """
    Return the path to the user's Desktop directory.

    Resolution order
    ────────────────
    Windows:
      1. Registry -> HKCU\\...\\User Shell Folders  "Desktop"
         (handles OneDrive redirects *and* localized folder names like "Escritorio")
      2. ~/OneDrive/Desktop
      3. ~/Desktop
      4. Home directory (ultimate fallback)

    macOS / Linux:
      1. ~/Desktop
      2. Home directory (ultimate fallback)
    """
    home = Path.home()

    if sys.platform == "win32":
        # ── 1. Windows Registry (most reliable) ──────────────────────
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            )
            raw_value, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)

            # The registry value may contain %USERPROFILE% or other env-vars.
            import os
            expanded = os.path.expandvars(raw_value)
            desktop = Path(expanded)

            if desktop.is_dir():
                return desktop
        except Exception:
            pass

        # ── 2. OneDrive-redirected Desktop ────────────────────────────
        onedrive_desktop = home / "OneDrive" / "Desktop"
        if onedrive_desktop.is_dir():
            return onedrive_desktop

    # ── 3. Standard ~/Desktop ─────────────────────────────────────
    standard_desktop = home / "Desktop"
    if standard_desktop.is_dir():
        return standard_desktop

    # ── 4. Ultimate fallback: home directory ──────────────────────
    return home


def generate_qr_code(url: str, filename: str) -> Path:
    """Generate a QR-code JPEG and return the saved file path."""
    desktop = get_desktop_path()

    if not filename.lower().endswith(".jpg"):
        filename = filename + ".jpg"

    output_path = desktop / filename

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img.save(str(output_path), format="JPEG")
    return output_path


def on_generate():
    url = url_entry.get().strip()
    filename = filename_entry.get().strip()

    if not url:
        messagebox.showerror("Error", "URL cannot be empty.")
        return

    if not filename:
        messagebox.showerror("Error", "Filename cannot be empty.")
        return

    save_dir = get_desktop_path()
    if not save_dir.is_dir():
        messagebox.showerror(
            "Error", f"Save directory not found at '{save_dir}'."
        )
        return

    try:
        output_path = generate_qr_code(url, filename)
        messagebox.showinfo(
            "Success", f"QR code saved successfully!\n\nPath: {output_path}"
        )
        url_entry.delete(0, tk.END)
        filename_entry.delete(0, tk.END)
    except Exception as exc:
        messagebox.showerror("Error", f"Failed to generate QR code:\n{exc}")


# --- Main window ---
root = tk.Tk()
root.title("QRX Desktop — QR Code Generator")
root.resizable(False, False)

# ── Fixed color palette (never changes with OS theme) ──
BG        = "#1c1c1e"   # window background
SURFACE   = "#3a3a3c"   # entry surface  (lighter so text is clearly readable)
ACCENT    = "#0a84ff"   # blue
ACCENT_DK = "#0060df"   # pressed blue
TEXT      = "#f2f2f7"   # primary text
SUBTEXT   = "#aeaeb2"   # muted text  (brighter than before for legibility)

FONT_TITLE    = ("Helvetica", 22, "bold")
FONT_SUBTITLE = ("Helvetica", 11)
FONT_LABEL    = ("Helvetica", 12, "bold")
FONT_ENTRY    = ("Helvetica", 13)
FONT_BUTTON   = ("Helvetica", 13, "bold")
FONT_HINT     = ("Helvetica", 10)

# Force Tk to stop inheriting system appearance
try:
    root.tk.call("tk", "scaling", 1.0)
    root.option_add("*Background", BG)
    root.option_add("*Foreground", TEXT)
    root.option_add("*Entry.Background", SURFACE)
    root.option_add("*Entry.Foreground", TEXT)
    root.option_add("*highlightBackground", BG)
except Exception:
    pass

root.configure(bg=BG)

# ── Title ──────────────────────────────────────────────
title_label = tk.Label(
    root,
    text="QRX Desktop",
    font=FONT_TITLE,
    bg=BG,
    fg=ACCENT,
)
title_label.grid(row=0, column=0, columnspan=2, pady=(28, 4))

subtitle_label = tk.Label(
    root,
    text="Generate QR codes from any URL",
    font=FONT_SUBTITLE,
    bg=BG,
    fg=SUBTEXT,
)
subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))

# ── URL field ──────────────────────────────────────────
url_label = tk.Label(
    root, text="URL / Link:", font=FONT_LABEL, bg=BG, fg=TEXT, anchor="w"
)
url_label.grid(row=2, column=0, sticky="w", padx=20, pady=(4, 4))

url_entry = tk.Entry(
    root,
    font=FONT_ENTRY,
    width=36,
    relief="flat",
    bd=0,
    bg=SURFACE,
    fg=TEXT,
    insertbackground=TEXT,
    selectbackground=ACCENT,
    selectforeground=TEXT,
    highlightthickness=2,
    highlightbackground=SURFACE,
    highlightcolor=ACCENT,
    disabledbackground=SURFACE,
    disabledforeground=SUBTEXT,
)
url_entry.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 12), ipady=8)

# ── Filename field ─────────────────────────────────────
filename_label = tk.Label(
    root,
    text="Output filename (no extension):",
    font=FONT_LABEL,
    bg=BG,
    fg=TEXT,
    anchor="w",
)
filename_label.grid(row=4, column=0, sticky="w", padx=20, pady=(4, 4))

filename_entry = tk.Entry(
    root,
    font=FONT_ENTRY,
    width=36,
    relief="flat",
    bd=0,
    bg=SURFACE,
    fg=TEXT,
    insertbackground=TEXT,
    selectbackground=ACCENT,
    selectforeground=TEXT,
    highlightthickness=2,
    highlightbackground=SURFACE,
    highlightcolor=ACCENT,
    disabledbackground=SURFACE,
    disabledforeground=SUBTEXT,
)
filename_entry.grid(row=5, column=0, columnspan=2, padx=20, pady=(0, 8), ipady=8)

# ── Hint (shows the actual resolved save directory) ────
_save_dir = get_desktop_path()
hint_label = tk.Label(
    root,
    text=f"File will be saved as .jpg to {_save_dir}",
    font=FONT_HINT,
    bg=BG,
    fg=SUBTEXT,
)
hint_label.grid(row=6, column=0, columnspan=2, pady=(0, 16))

# ── Generate button (Label-based so macOS can't override colors) ───
btn_frame = tk.Frame(root, bg=ACCENT, cursor="hand2")
btn_frame.grid(row=7, column=0, columnspan=2, pady=(0, 28))

btn_label = tk.Label(
    btn_frame,
    text="Generate QR Code",
    font=FONT_BUTTON,
    bg=ACCENT,
    fg=TEXT,
    padx=32,
    pady=12,
    cursor="hand2",
)
btn_label.pack()


def _btn_hover(e):
    btn_frame.configure(bg=ACCENT_DK)
    btn_label.configure(bg=ACCENT_DK)


def _btn_leave(e):
    btn_frame.configure(bg=ACCENT)
    btn_label.configure(bg=ACCENT)


def _btn_click(e):
    on_generate()


btn_label.bind("<Enter>", _btn_hover)
btn_label.bind("<Leave>", _btn_leave)
btn_label.bind("<Button-1>", _btn_click)
btn_frame.bind("<Enter>", _btn_hover)
btn_frame.bind("<Leave>", _btn_leave)
btn_frame.bind("<Button-1>", _btn_click)

root.mainloop()
