# Prototype Naturo Product Lookup - Tkinter UI
# Save as main.py and run with: python main.py
# Requires: Pillow (PIL)
# Install with: pip install pillow
# This app scans /mnt/data by default. Change ROOT_DIR to your dataset folder if needed.

from PIL import Image, ImageTk
import os, re, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ROOT_DIR = "/Users/nikhil/Downloads/Naturo Experience Center Paharganj"  # change this if running elsewhere

# Supported image extensions
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

def scan_images(root_dir):
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower().endswith(IMG_EXTS):
                full = os.path.join(dirpath, fn)
                files.append(full)
    return files

# Build a lightweight searchable index of filenames (lowercased)
all_images = scan_images(ROOT_DIR)
index = []
for p in all_images:
    index.append({
        "path": p,
        "name": os.path.basename(p),
        "searchable": re.sub(r'[^0-9A-Za-z_]+', '_', os.path.basename(p)).lower()
    })

# Helper: naive tokenization of user product code input
def tokenize_code(code):
    if not code: return []
    # normalize separators to underscores and split
    s = re.sub(r'[^0-9A-Za-z_]+', '_', code).lower()
    tokens = [t for t in s.split('_') if t]
    return tokens

# Search strategy (prototype):
# - Tokenize input code into tokens
# - A file matches if at least 60% of non-trivial tokens appear in the filename searchable text
def search_files(code):
    tokens = tokenize_code(code)
    if not tokens:
        return [it["path"] for it in index]  # show all if empty
    matched = []
    for it in index:
        found = 0
        for t in tokens:
            if len(t) <= 1: continue
            if t in it["searchable"]:
                found += 1
        # require at least 60% tokens (or at least 2 tokens) to match
        if len(tokens) == 0: continue
        score = found / len(tokens)
        if score >= 0.6 or found >= 2:
            matched.append((score, it["path"]))
    # sort by score desc then name
    matched.sort(key=lambda x: (-x[0], x[1]))
    return [m[1] for m in matched]

# --- Build Tkinter UI ---
class NaturoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Naturo Product Lookup - Prototype")
        self.geometry("1000x700")
        self.configure(bg="#f3f4f6")
        self.setup_ui()
        self.current_image = None

    def setup_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Top input row
        top = ttk.Frame(frm)
        top.pack(fill="x", pady=(0,8))
        ttk.Label(top, text="Enter full product code:", font=("Segoe UI", 11)).pack(side="left")
        self.entry = ttk.Entry(top, width=70)
        self.entry.pack(side="left", padx=(8,6))
        self.entry.insert(0, "e.g. 24_PK_PV_BR_MRP_975_FT_Pr_Eq_14L_12\"9.5F_02_KYGH_Q8")
        btn = ttk.Button(top, text="Search", command=self.on_search)
        btn.pack(side="left")

        # Left: results list
        left = ttk.Frame(frm)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Matches", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.listbox = tk.Listbox(left, width=50, height=30)
        self.listbox.pack(side="left", fill="y", padx=(0,6))
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Right: image display & metadata
        right = ttk.Frame(frm)
        right.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(right, bg="white")
        self.canvas.pack(fill="both", expand=True)
        bottom = ttk.Frame(right)
        bottom.pack(fill="x")
        self.meta = ttk.Label(bottom, text="No selection", anchor="w")
        self.meta.pack(fill="x")

        # Populate initial list with all images
        self.populate_list([it["path"] for it in index])

    def populate_list(self, paths):
        self.listbox.delete(0, tk.END)
        for p in paths:
            self.listbox.insert(tk.END, p)

    def on_search(self):
        code = self.entry.get().strip()
        results = search_files(code)
        if not results:
            messagebox.showinfo("No results", "No matching files found for that code.")
        self.populate_list(results)

    def on_select(self, evt):
        sel = self.listbox.curselection()
        if not sel: return
        path = self.listbox.get(sel[0])
        self.show_image(path)

    def show_image(self, path):
        try:
            img = Image.open(path)
            # resize to fit canvas while keeping aspect ratio
            cw = self.canvas.winfo_width() or 600
            ch = self.canvas.winfo_height() or 400
            iw, ih = img.size
            scale = min(cw/iw, ch/ih, 1.6)
            nw = int(iw*scale)
            nh = int(ih*scale)
            img2 = img.resize((nw, nh), Image.LANCZOS)
            self.current_image = ImageTk.PhotoImage(img2)
            self.canvas.delete("all")
            self.canvas.create_image(cw//2, ch//2, image=self.current_image, anchor="center")
            self.meta.config(text=f"{os.path.basename(path)}  —  {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

if __name__ == '__main__':
    app = NaturoApp()
    app.mainloop()
