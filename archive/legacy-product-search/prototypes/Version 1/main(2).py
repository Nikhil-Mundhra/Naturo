# Prototype Naturo Product Lookup - Tkinter UI (Updated stricter matching)
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

# Known code lists (lowercase)
MATERIAL_CODES = {
    'ch','pv','wp','ft','eq','l','s','dt','tx','dms','fms','bmdm','sl','sphv','uvfs','uvmb','pl','wd','dmgl','h3d','mtt','lv','pr','rd','acy'
}
# Colour codes (common ones from your sheet)
COLOR_CODES = {
    'rd','bl','gd','tk','wl','yl','st','gy','br','pl','gn','rg','bg','cr','mo','mt','mb','wt','sv','bk','bk'  # include black as bk etc.
}

def scan_images(root_dir):
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower().endswith(IMG_EXTS):
                full = os.path.join(dirpath, fn)
                files.append(full)
    return files

# Build a lightweight searchable index of filenames (lowercased, non-alnum -> underscore)
def make_searchable(name):
    return re.sub(r'[^0-9A-Za-z_]+', '_', name).lower()

all_images = scan_images(ROOT_DIR)
index = []
for p in all_images:
    index.append({
        "path": p,
        "name": os.path.basename(p),
        "searchable": make_searchable(os.path.basename(p))
    })

# Helper: normalize input and split into tokens
def normalize_input(code):
    if not code: return []
    s = re.sub(r'[^0-9A-Za-z_"]+', '_', code)  # keep double-quote for size detection
    # collapse multiple underscores
    s = re.sub(r'__+', '_', s)
    tokens = [t for t in s.split('_') if t]
    return tokens

# Detect material / colour / size tokens from input tokens
def parse_product_code(code):
    tokens = normalize_input(code)
    tokens_lc = [t.lower().replace('"','_') for t in tokens]  # make a version with quote->underscore
    material = [t for t in tokens_lc if t in MATERIAL_CODES]
    color = [t for t in tokens_lc if t in COLOR_CODES]
    # size detection: look for tokens containing digits and 'f' (feet) e.g. 12"9.5f, 12_9_5f, 12_9.5f
    size = []
    for t in tokens:
        tl = t.lower()
        # normalize quotes and dots to underscore
        norm = re.sub(r'["\.]', '_', tl)
        # replace any non-alnum/underscore with underscore and collapse
        norm = re.sub(r'[^0-9a-z_]+', '_', norm)
        norm = re.sub(r'__+', '_', norm)
        # common pattern: starts with digits and contains 'f' (foot) or ends with 'f'
        if re.search(r'\d+_?\d+.*f', norm) or ('f' in norm and re.search(r'\d', norm)):
            size.append(norm)
    # Also create canonical size tokens from any found like 12_9_5f
    size_canonical = []
    for s in size:
        s2 = s.replace('"','_').replace('.', '_')
        s2 = re.sub(r'__+', '_', s2).lower()
        size_canonical.append(s2)
    # remove duplicates
    return {
        "tokens": [t.lower() for t in tokens],
        "material": list(dict.fromkeys(material)),
        "color": list(dict.fromkeys(color)),
        "size": list(dict.fromkeys(size_canonical))
    }

# Strict matching strategy:
# - If material tokens present in input, require file to contain at least one material token
# - If color tokens present, require file to contain at least one color token
# - If size tokens present, require file to contain a normalized size token
# - After filtering by the required fields, rank by how many remaining tokens match
def search_files_strict(code):
    parsed = parse_product_code(code)
    tokens = [re.sub(r'[^0-9A-Za-z]+', '', t).lower() for t in parsed["tokens"] if t]
    required_materials = parsed["material"]
    required_colors = parsed["color"]
    required_sizes = parsed["size"]

    matched = []
    for it in index:
        s = it["searchable"]
        # check material requirement
        if required_materials:
            ok_mat = any(mat in s for mat in required_materials)
            if not ok_mat:
                continue
        # check color requirement
        if required_colors:
            ok_col = any(col in s for col in required_colors)
            if not ok_col:
                continue
        # check size requirement - sizes might appear with underscores and dots replaced
        if required_sizes:
            ok_size = False
            for sz in required_sizes:
                # create variants to test against searchable name
                variants = set()
                variants.add(sz)
                variants.add(sz.replace('_', ''))  # 1295f
                variants.add(sz.replace('_','_'))  # same
                # also try replacing final 'f' forms (e.g., 12_9_5f vs 12_9_5)
                variants.add(sz.rstrip('f'))
                # check if any variant in searchable
                for v in variants:
                    if v and v in s:
                        ok_size = True
                        break
                if ok_size: break
            if not ok_size:
                continue

        # passed mandatory filters — compute score based on how many tokens match
        found = 0
        for t in tokens:
            if len(t) <= 1: continue
            if t in s:
                found += 1
        score = found / max(1, len(tokens))
        matched.append((score, it["path"]))

    # sort by score desc then name
    matched.sort(key=lambda x: (-x[0], x[1]))
    return [m[1] for m in matched]

# Fallback to fuzzy search (old behavior)
def search_files_fuzzy(code):
    # keep old behavior for cases without material/color/size
    tokens = [t for t in re.sub(r'[^0-9A-Za-z_]+', '_', code).lower().split('_') if t]
    if not tokens:
        return [it["path"] for it in index]
    matched = []
    for it in index:
        found = 0
        for t in tokens:
            if len(t) <= 1: continue
            if t in it["searchable"]:
                found += 1
        score = found / len(tokens) if tokens else 0
        if score >= 0.6 or found >= 2:
            matched.append((score, it["path"]))
    matched.sort(key=lambda x: (-x[0], x[1]))
    return [m[1] for m in matched]

# Wrapper: choose strict search when material/color/size present, otherwise fuzzy
def search_files(code):
    parsed = parse_product_code(code)
    if parsed["material"] or parsed["color"] or parsed["size"]:
        res = search_files_strict(code)
        # if strict returns nothing, fallback to fuzzy
        if res:
            return res
        else:
            return search_files_fuzzy(code)
    else:
        return search_files_fuzzy(code)

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
        self.entry.insert(0, 'e.g. 24_PK_PV_BR_MRP_975_FT_Pr_Eq_14L_12\"9.5F_02_KYGH_Q8')
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
