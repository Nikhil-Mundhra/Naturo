# config.py

import json
import os
from .constants import CONFIG_FILE

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def pick_root_dir():
    try:
        from PySide6.QtWidgets import QFileDialog
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setOption(QFileDialog.ShowDirsOnly, True)
        if dlg.exec():
            return dlg.selectedFiles()[0]
    except ImportError:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            folder = filedialog.askdirectory()
            root.destroy()
            return folder if folder else None
        except Exception:
            pass
    return None
