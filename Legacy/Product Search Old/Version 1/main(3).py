# Naturo Product Lookup - Prototype (Supplier-folder-first)
# Save as main.py and run with: python main.py
# Requires: Pillow (PIL)
# Install with: pip install pillow
# This app scans ROOT_DIR for images and attempts to find supplier folder -> selected -> folder code (e.g., "02")
# Then searches inside that folder for matching images by material, color, size and other tokens.

from PIL import Image, ImageTk
import os, re, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ROOT_DIR = "/Users/nikhil/Downloads/Naturo Experience Center Paharganj"  # change this to your dataset root when running locally

# Supported image extensions
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

# Known code lists (lowercase) - extend as needed or load from CSV later
MATERIAL_CODES = {
    'ch','pv','wp','ft','eq','l','s','dt','tx','dms','fms','bmdm','sl','sphv','uvfs','uvmb','pl','wd','dmgl','h3d','mtt','lv','pr','rd','acy'
}
COLOR_CODES = {
    'rd','bl','gd','tk','wl','yl','st','gy','br','pl','gn','rg','bg','cr','mo','mt','mb','wt','sv','bk'
}

# --- filesystem index ---
def scan_images(root_dir):
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower().endswith(IMG_EXTS):
                full = os.path.join(dirpath, fn)
                files.append(full)
    return files

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

# Build a directory list for supplier-folder lookup
all_dirs = set()
for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
    all_dirs.add(dirpath)
all_dirs = list(all_dirs)

# --- parsing helpers ---
def normalize_token_for_search(t):
    return re.sub(r'[^0-9a-z]+', '_', t.lower())

def normalize_input(code):
    if not code: return []
    s = re.sub(r'[^0-9A-Za-z_"]+', '_', code)  # keep double-quote for size detection
    s = re.sub(r'__+', '_', s)
    tokens = [t for t in s.split('_') if t]
    return tokens

def parse_product_code(code):
    tokens = normalize_input(code)
    tokens_lc = [t.lower().replace('"','_') for t in tokens]
    material = [t for t in tokens_lc if t in MATERIAL_CODES]
    color = [t for t in tokens_lc if t in COLOR_CODES]
    # supplier and folder code heuristics: if last token starts with q (Q8) treat supplier as -2 and folder as -3
    supplier = None
    folder_code = None
    if len(tokens) >= 2:
        last = tokens[-1].lower()
        if re.match(r'^[qq]\d+|^q\d+|^q\w+', last) or re.match(r'^q\d+', last):
            # handle 'Q8' like tokens
            if len(tokens) >= 3:
                supplier = tokens[-2]
            if len(tokens) >= 4:
                folder_code = tokens[-3]
        else:
            # fallback: supplier = last token, folder = second last
            supplier = tokens[-1]
            if len(tokens) >= 2:
                folder_code = tokens[-2]
    # size detection
    size = []
    for t in tokens:
        tl = t.lower()
        norm = re.sub(r'["\.]', '_', tl)
        norm = re.sub(r'[^0-9a-z_]+', '_', norm)
        norm = re.sub(r'__+', '_', norm)
        if re.search(r'\d+_?\d*.*f', norm) or ('f' in norm and re.search(r'\d', norm)):
            size.append(norm)
    size_canonical = []
    for s in size:
        s2 = s.replace('"','_').replace('.', '_')
        s2 = re.sub(r'__+', '_', s2).lower()
        size_canonical.append(s2)
    return {
        "tokens": [t.lower() for t in tokens],
        "material": list(dict.fromkeys(material)),
        "color": list(dict.fromkeys(color)),
        "size": list(dict.fromkeys(size_canonical)),
        "supplier": supplier.lower() if supplier else None,
        "folder_code": folder_code.lower() if folder_code else None
    }

# --- supplier & folder search ---
def find_supplier_selected_folder(supplier_code):
    if not supplier_code:
        return None
    sc = supplier_code.lower()
    candidates = []
    for d in all_dirs:
        bn = os.path.basename(d).lower()
        if sc in bn:
            candidates.append(d)
    # prefer the candidate that contains a 'selected' subfolder
    for c in candidates:
        for root, dirs, files in os.walk(c):
            for sub in dirs:
                if 'selected' in sub.lower():
                    return os.path.join(root, sub)
    # if none with 'selected', return first candidate
    if candidates:
        return candidates[0]
    return None

def find_folder_with_code(parent_dir, folder_code):
    if not parent_dir or not folder_code:
        return None
    fc = folder_code.lower()
    # search only inside parent_dir subtree for a dir that contains folder_code as token
    for root, dirs, files in os.walk(parent_dir):
        for d in dirs:
            dn = d.lower()
            searchable = re.sub(r'[^0-9a-z]+','_', dn)
            # check token boundary: _02_ or startswith 02_ or endswith _02 or equals 02
            if re.search(r'(^|_)' + re.escape(fc) + r'(_|$)', searchable):
                return os.path.join(root, d)
    return None

# --- matching strategies ---
def matches_size_in_searchable(searchable, required_sizes):
    # check variants for size tokens like 12_9_5f and 12_9_5
    for sz in required_sizes:
        v1 = sz
        v2 = sz.replace('_','')
        v3 = sz.rstrip('f')
        variants = {v1, v2, v3}
        for v in variants:
            if v and v in searchable:
                return True
    return False

def search_files_strict(code):
    parsed = parse_product_code(code)
    required_materials = parsed["material"]
    required_colors = parsed["color"]
    required_sizes = parsed["size"]
    supplier = parsed["supplier"]
    folder_code = parsed["folder_code"]

    # Step 1: if supplier present, find supplier_selected_folder
    search_root = ROOT_DIR
    if supplier:
        sup_folder = find_supplier_selected_folder(supplier)
        if sup_folder:
            # next, find the folder that contains the folder_code inside supplier's Selected folder
            fc_folder = find_folder_with_code(sup_folder, folder_code) if folder_code else None
            if fc_folder:
                search_root = fc_folder
            else:
                search_root = sup_folder

    # Build a list of candidate files under search_root
    candidate_files = []
    for dirpath, dirnames, filenames in os.walk(search_root):
        for fn in filenames:
            if fn.lower().endswith(IMG_EXTS):
                candidate_files.append(os.path.join(dirpath, fn))

    # Now filter candidate_files with strict conditions
    matched = []
    tokens = [re.sub(r'[^0-9A-Za-z]+', '', t).lower() for t in parsed["tokens"] if t]
    for p in candidate_files:
        s = make_searchable(os.path.basename(p))
        # material
        if required_materials:
            if not any(mat in s for mat in required_materials):
                continue
        # color
        if required_colors:
            if not any(col in s for col in required_colors):
                continue
        # size
        if required_sizes:
            if not matches_size_in_searchable(s, required_sizes):
                continue
        # passed required filters - score by token matches
        found = 0
        for t in tokens:
            if len(t) <= 1: continue
            if t in s:
                found += 1
        score = found / max(1, len(tokens))
        matched.append((score, p))

    matched.sort(key=lambda x: (-x[0], x[1]))
    return [m[1] for m in matched]

def search_files_fuzzy(code):
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

def search_files(code):
    parsed = parse_product_code(code)
    if parsed["material"] or parsed["color"] or parsed["size"] or parsed["supplier"] or parsed["folder_code"]:
        res = search_files_strict(code)
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
        self.title("Naturo Product Lookup - Prototype (Supplier-folder-first)")
        self.geometry("1100x740")
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
        self.entry = ttk.Entry(top, width=80)
        self.entry.pack(side="left", padx=(8,6))
        self.entry.insert(0, 'e.g. 24_PK_PV_BR_MRP_975_FT_Pr_Eq_14L_12"9.5F_02_KYGH_Q8')
        btn = ttk.Button(top, text="Search", command=self.on_search)
        btn.pack(side="left")

        # Left: results list
        left = ttk.Frame(frm)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Matches", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.listbox = tk.Listbox(left, width=60, height=34)
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
        # show where search was performed (helpful)
        parsed = parse_product_code(code)
        sr = parsed.get("supplier"), parsed.get("folder_code")
        print("Search parsed supplier/folder:", sr)

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
