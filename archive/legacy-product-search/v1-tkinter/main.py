# naturo_search_final.py
# Naturo Surfaces App - PySide6 (stable: persistent bottom controls, cleaned design toolbox)
# pip install PySide6 pillow
# python naturo_search_final.py
# eg: 24_PK_PV_BR_MRP_975_FT_Pr_Eq_14L_12"9.5F_02_KYGH_Q8

import sys
import os
import re
import json
from PIL import Image, ImageQt
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem, QComboBox, QFormLayout,
    QStackedWidget, QSplitter, QMessageBox, QFileDialog, QRadioButton,
    QButtonGroup, QSizePolicy, QToolBox, QScrollArea, QCheckBox,
    QDialog, QTextEdit
)
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap, QGuiApplication

# ---------------- CONFIG ----------------
CONFIG_FILE = "naturo_config.json"
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

# color/material/design maps (full name -> code)
COLOR_MAP = {
    "Red": "RD", "Black": "BL", "Gold": "GD", "Silver": "SV", "Teak": "TK",
    "Walnut": "WL", "Yellow": "YL", "Blue": "BU", "Steel": "ST", "Grey": "GY",
    "Brown": "BR", "White": "WT", "Purple": "PL", "Green": "GN", "Rose Gold": "RG",
    "Beage": "BG", "Cream": "CR", "Mobe": "MO", "Metalic": "MT", "Marble": "MB"
}

MATERIAL_MAP = {
    "Charcoal": "CH",
    "PVC": "PV",
    "WPC": "WP",
    "Super Heavy": "SPHV",
    "Ultra Voilet Foarm Sheet": "UVFS",
    "Ultra Voilet Marble Sheet": "UVMB",
    "Tiger Fabric": "TG",
    "Acrylic": "ACY"
}

# grouping for collapsible design selector
DESIGN_CATEGORIES = {
    "Pattern Type": {
        "Flutted": "FT",
        "Equal Distance Between The Lines": "EQ",
        "Line": "L",
        "Step": "S",
        "Double Tone": "DT",
        "Rounded": "RD",
        "Louver Style": "LV"
    },
    "Surface Finish": {
        "Texture": "TX",
        "Matt": "MTT",
        "Seamless": "SL",
        "Printed": "PR",
        "Wooden": "WD"
    },
    "Special Types": {
        "Digital Marble Sheet": "DMS",
        "Flutted Marble Sheet": "FMS",
        "Book Match Digital Marble": "BMDM",
        "Digital Marble Gold Line": "DMGL",
        "High/3D Sheet": "H3D",
        "Panel No Line": "PL",
        "Volume": "VO",
        "Catalogue": "CT"
    }
}

# design flat map (name -> code) derived
DESIGN_MAP = {}
for cat in DESIGN_CATEGORIES.values():
    DESIGN_MAP.update(cat)

# heights
HEIGHT_COLLAPSED_QN = 65
HEIGHT_SEARCH = 120
HEIGHT_QN = 900

# ---------------- UTILS / PARSING ----------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

def pick_root_dir():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.Directory)
    dlg.setOption(QFileDialog.ShowDirsOnly, True)
    if dlg.exec():
        folder = dlg.selectedFiles()[0]
        return folder
    return None

def scan_images(root_dir):
    """
    Recursively scan images under root_dir.
    Returns list of file paths.
    """
    files = []
    if not root_dir or not os.path.exists(root_dir):
        return files
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower().endswith(IMG_EXTS):
                files.append(os.path.join(dirpath, fn))
    return files

def make_searchable(name):
    return re.sub(r'[^0-9A-Za-z_]+', '_', name).lower()

def normalize_size_token(s):
    if not s:
        return s
    x = s.replace('"', '_').replace('.', '_').replace(' ', '_')
    x = re.sub(r'__+', '_', x)
    return x.lower()

def normalize_input(code):
    s = re.sub(r'[^0-9A-Za-z_"]+', '_', code)
    s = re.sub(r'__+', '_', s)
    return [t for t in s.split('_') if t]

def parse_product_code(code: str):
    """
    Parse a full product code into structured tokens.
    Rules:
      - Everything before the material code (PV/CH/...) is treated as the prefix (e.g. '24_PK')
      - Do NOT split the prefix into '24' and 'PK'
      - Material, color, size, supplier, folder_code, and file token are extracted
    """
    tokens = normalize_input(code)

    # prefix = everything until the first material code
    material_codes = [v.lower() for v in MATERIAL_MAP.values()]
    color_codes = [v.lower() for v in COLOR_MAP.values()]

    prefix = []
    material = []
    color = []
    supplier = None
    folder_code = None
    file_token = None
    size = []

    found_material = False
    for t in tokens:
        tl = t.lower()
        if not found_material and tl in material_codes:
            found_material = True
            material.append(tl)
            continue
        if not found_material:
            prefix.append(t)
            continue
        if tl in material_codes:
            material.append(tl)
        elif tl in color_codes:
            color.append(tl)
        elif re.search(r'\d+[fl]', tl):  # size like 12f, 9.5f, 14l
            size.append(normalize_size_token(tl))
        else:
            # keep last two tokens for supplier & folder
            if not folder_code:
                folder_code = tl
            elif not supplier:
                supplier = tl
            else:
                file_token = tl

    return {
        "prefix": "_".join(prefix) if prefix else None,
        "material": material,
        "color": color,
        "size": size,
        "supplier": supplier,
        "folder_code": folder_code,
        "file_token": file_token,
        "tokens": tokens
    }

# ---------------- SEARCH HELPERS ----------------
def build_dir_index(root_dir):
    return {d for d, _, _ in os.walk(root_dir)}

def find_supplier_selected_folder(root_dir, supplier_code):
    """
    Find the 'Selected Item' folder for a given supplier code.
    Looks for folder names containing supplier_code (case-insensitive).
    If multiple matches, prioritizes one containing 'Selected' in its path.
    """
    if not supplier_code:
        return None

    sc = supplier_code.lower()
    selected_candidate = None
    fallback_candidate = None

    for dirpath, dirnames, _ in os.walk(root_dir):
        base = os.path.basename(dirpath).lower()
        if sc in base:
            # Prefer "Selected" folder
            if "selected" in base:
                return dirpath
            # Check subfolders for 'selected'
            for d in dirnames:
                if "selected" in d.lower():
                    return os.path.join(dirpath, d)
            if not fallback_candidate:
                fallback_candidate = dirpath

        # Also check subfolders
        for d in dirnames:
            if sc in d.lower() and "selected" in d.lower():
                return os.path.join(dirpath, d)

    return fallback_candidate or selected_candidate

def find_folder_with_code(parent_dir, folder_code, supplier_prefix=None):
    """
    Finds the folder matching the folder_code.
    If found, also checks one level deeper for supplier_prefix or folder_code again.
    """
    if not parent_dir or not folder_code:
        return None

    fc = folder_code.lower()
    sp = supplier_prefix.lower() if supplier_prefix else None

    for root, dirs, _ in os.walk(parent_dir):
        for d in dirs:
            searchable = re.sub(r'[^0-9a-z]+', '_', d.lower())
            if re.search(r'(^|_)' + re.escape(fc) + r'(_|$)', searchable):
                candidate = os.path.join(root, d)

                # --- drill one more level ---
                subdirs = [os.path.join(candidate, sd) for sd in os.listdir(candidate) if os.path.isdir(os.path.join(candidate, sd))]
                for sub in subdirs:
                    sub_base = re.sub(r'[^0-9a-z]+', '_', os.path.basename(sub).lower())
                    if (sp and sp in sub_base) or re.search(r'(^|_)' + re.escape(fc) + r'(_|$)', sub_base):
                        return sub

                return candidate
    return None

def color_matches(searchable, required_colors):
    for col in required_colors:
        if re.search(r'(^|_)' + re.escape(col) + r'(_|$)', searchable):
            return True
        if col in searchable:
            return True
    return False

def matches_size(searchable, required_sizes):
    for sz in required_sizes:
        v1 = sz.lower()
        v2 = v1.replace('_', '')
        v3 = v1.rstrip('f').rstrip('l')
        for v in (v1, v2, v3):
            if v and v in searchable:
                return True
    return False

def debug_search_files_wrapper(root_dir, code):
    print("\n=== DEBUG SEARCH START ===")
    print(f"Search Code: {code}")
    parsed = parse_product_code(code)
    print("Parsed Tokens:", parsed)

    supplier = parsed["supplier"]
    folder_code = parsed["folder_code"]
    required_materials = parsed["material"]
    required_colors = parsed["color"]
    required_sizes = parsed["size"]

    search_root = root_dir
    if supplier:
        sup_folder = find_supplier_selected_folder(root_dir, supplier)
        print(f"Supplier folder: {sup_folder}")
        if sup_folder:
            fc_folder = find_folder_with_code(sup_folder, folder_code) if folder_code else None
            print(f"Folder code folder: {fc_folder}")
            search_root = fc_folder or sup_folder

    print(f"Final search root: {search_root}")
    candidate_files = scan_images(search_root)
    print(f"Total candidate files: {len(candidate_files)}")

    results = []
    for p in candidate_files:
        s = make_searchable(os.path.basename(p))
        reasons = []
        if required_materials and not any(mat in s for mat in required_materials):
            reasons.append("Material mismatch")
        if required_colors and not any(re.search(r'(^|_)' + re.escape(col) + r'($|_)', s) or re.search(col, s) for col in required_colors):
            reasons.append("Color mismatch")
        if required_sizes and not matches_size(s, required_sizes):
            reasons.append("Size mismatch")

        if reasons:
            print(f"SKIP: {os.path.basename(p)} -> {', '.join(reasons)}")
            continue

        results.append(p)

    print(f"Matches found: {len(results)}")
    for r in results:
        print("MATCH:", r)

    print("=== DEBUG SEARCH END ===\n")
    return results

def search_files(root_dir, code):
    """
    Search for image files based on parsed product code.
    Navigates supplier -> folder_code, then filters filenames.
    """
    parsed = parse_product_code(code)
    supplier = parsed["supplier"]
    folder_code = parsed["folder_code"]
    material = parsed["material"]
    color = parsed["color"]
    size = parsed["size"]
    file_token = parsed["file_token"]

    # Step 1: Supplier
    search_root = root_dir
    if supplier:
        sup_folder = find_supplier_selected_folder(root_dir, supplier)
        if sup_folder:
            search_root = sup_folder

    # Step 2: Folder code inside supplier folder
    if folder_code:
        fc_folder = find_folder_with_code(search_root, folder_code)
        if fc_folder:
            search_root = fc_folder

    # Step 3: Gather all image candidates inside resolved folder
    candidate_files = scan_images(search_root)
    results = []

    # Step 4: Match filtering
    for p in candidate_files:
        s = make_searchable(os.path.basename(p))
        if material and not any(m in s for m in material):
            continue
        if color and not color_matches(s, color):
            continue
        if size and not matches_size(s, size):
            continue
        if file_token and file_token not in s:
            continue
        results.append(p)

    return results

def debug_search_files(root_dir, code, max_show=40):
    """
    Debug version of search_files, prints reasoning for matches/rejections.
    """
    parsed = parse_product_code(code)
    supplier = parsed["supplier"]
    folder_code = parsed["folder_code"]
    material = parsed["material"]
    color = parsed["color"]
    size = parsed["size"]
    file_token = parsed["file_token"]

    search_root = root_dir
    sup_folder = None
    fc_folder = None

    if supplier:
        sup_folder = find_supplier_selected_folder(root_dir, supplier)
        if sup_folder:
            search_root = sup_folder
    if folder_code:
        fc_folder = find_folder_with_code(search_root, folder_code)
        if fc_folder:
            search_root = fc_folder

    candidate_files = scan_images(search_root)
    matches, reasons = [], []
    for p in candidate_files:
        s = make_searchable(os.path.basename(p))
        fail_reasons = []
        if material and not any(m in s for m in material):
            fail_reasons.append("material")
        if color and not color_matches(s, color):
            fail_reasons.append("color")
        if size and not matches_size(s, size):
            fail_reasons.append("size")
        if file_token and file_token not in s:
            fail_reasons.append("file_token")
        if fail_reasons:
            reasons.append((p, fail_reasons))
        else:
            matches.append(p)

    debug = {
        "parsed": parsed,
        "search_root": search_root,
        "supplier_folder_found": sup_folder,
        "folder_code_folder_found": fc_folder,
        "candidate_count": len(candidate_files),
        "matches_count": len(matches),
        "matches": matches[:max_show],
        "rejections": reasons[:max_show]
    }
    return debug, matches

# ---------------- UI ----------------
class DebugDialog(QDialog):
    def __init__(self, debug_info):
        super().__init__()
        self.setWindowTitle("Debug Info")
        self.resize(900, 600)
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setReadOnly(True)
        content = []
        content.append("Parsed input:")
        content.append(json.dumps(debug_info["parsed"], indent=2))
        content.append("")
        content.append(f"Search root: {debug_info['search_root']}")
        content.append(f"Supplier-folder found: {debug_info.get('supplier_folder_found')}")
        content.append(f"Folder-code folder found: {debug_info.get('folder_code_folder_found')}")
        content.append("")
        content.append(f"Candidate files scanned: {debug_info['candidate_count']}")
        content.append(f"Matching files found: {debug_info['matches_count']} (showing up to {len(debug_info['matches'])})")
        content.append("Matches:")
        for m in debug_info["matches"]:
            content.append(" - " + m)
        content.append("")
        content.append("Sample rejections (file -> missing parts):")
        for p, reasons in debug_info["rejections"]:
            content.append(" - " + p + " -> missing: " + ",".join(reasons))
        text.setText("\n".join(content))
        layout.addWidget(text)
        self.setLayout(layout)

class SearchTab(QWidget):
    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = root_dir
        layout = QVBoxLayout()

        # Toggle buttons (mode)
        toggle_row = QHBoxLayout()
        self.code_radio = QRadioButton("Product Code Search")
        self.qn_radio = QRadioButton("Questionnaire Search")
        self.code_radio.setChecked(True)
        self.toggle_group = QButtonGroup()
        self.toggle_group.addButton(self.code_radio)
        self.toggle_group.addButton(self.qn_radio)
        toggle_row.addWidget(self.code_radio)
        toggle_row.addWidget(self.qn_radio)
        toggle_row.addStretch()

        # Stack widgets for modes
        self.stack = QStackedWidget()

        # --- Code search UI ---
        code_widget = QWidget()
        code_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter full product code...")
        code_layout.addWidget(self.search_input)
        code_widget.setLayout(code_layout)

        # --- Questionnaire UI ---
        qn_widget = QWidget()

        # ===== LEFT COLUMN =====
        left_form = QFormLayout()

        # Material
        self.material_cb = QComboBox()
        self.material_cb.addItems([""] + list(MATERIAL_MAP.keys()))
        left_form.addRow("Material:", self.material_cb)

        # Height dropdown
        self.height_cb = QComboBox()
        self.height_cb.addItems(["", '8F', '9F', '9.5F'])
        left_form.addRow("Height:", self.height_cb)

        # Width entry
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText('Width in inches')
        left_form.addRow("Width:", self.width_input)

        # Colour
        self.color_cb = QComboBox()
        self.color_cb.addItems([""] + list(COLOR_MAP.keys()))
        left_form.addRow("Colour:", self.color_cb)

        left_widget = QWidget()
        left_widget.setLayout(left_form)

        # ===== RIGHT COLUMN: DESIGN TOOLBOX =====
        self.design_toolbox = QToolBox()
        self.design_checkboxes = {}
        for cat, designs in DESIGN_CATEGORIES.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            container = QWidget()

            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(2)

            cb_list = []
            for name in designs.keys():
                cb = QCheckBox(name)
                cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addWidget(cb)
                row_layout.addStretch()
                vbox.addLayout(row_layout)
                cb_list.append(cb)

            vbox.addStretch()
            scroll.setWidget(container)
            self.design_toolbox.addItem(scroll, cat)
            self.design_checkboxes[cat] = cb_list

        right_widget = self.design_toolbox

        # ===== TOP HORIZONTAL SPLIT =====
        top_cols = QHBoxLayout()
        top_cols.setContentsMargins(0, 0, 0, 0)
        top_cols.setSpacing(10)
        top_cols.addWidget(left_widget, 1)
        top_cols.addWidget(right_widget, 2)

        # ===== MAIN VERTICAL STACK (no per-mode buttons here) =====
        qn_main_vbox = QVBoxLayout()
        qn_main_vbox.setContentsMargins(0, 0, 0, 0)
        qn_main_vbox.setSpacing(5)
        qn_main_vbox.addLayout(top_cols)
        qn_widget.setLayout(qn_main_vbox)

        self.stack.addWidget(code_widget)
        self.stack.addWidget(qn_widget)

        # Top widget with animation (collapsible)
        self.top_widget = QWidget()
        top_panel = QVBoxLayout()
        top_panel.addLayout(toggle_row)
        top_panel.addWidget(self.stack)
        self.top_widget.setLayout(top_panel)
        self.top_widget.setMaximumHeight(HEIGHT_SEARCH)
        self.top_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.height_anim = QPropertyAnimation(self.top_widget, b"maximumHeight")
        self.height_anim.setDuration(300)

        # Active filters label (always visible, under top panel)
        self.active_filters_label = QLabel("")
        self.active_filters_label.setStyleSheet("font-weight: bold; padding: 6px;")

        # ===== PERSISTENT CONTROL ROW (always visible; works in both modes) =====
        controls_row = QHBoxLayout()
        controls_row.addStretch()
        self.search_btn_main = QPushButton("Search")
        self.clear_btn_main = QPushButton("Clear All")
        self.add_to_cart_btn = QPushButton("Add Selected to Cart")
        controls_row.addWidget(self.search_btn_main)
        controls_row.addWidget(self.clear_btn_main)
        controls_row.addWidget(self.add_to_cart_btn)
        controls_row.addStretch()

        self.search_btn_main.clicked.connect(self.search_clicked)
        self.clear_btn_main.clicked.connect(self.master_clear_all)
        self.add_to_cart_btn.clicked.connect(self.add_selected_to_cart)

        # Results & preview area
        self.splitter = QSplitter(Qt.Horizontal)
        self.results_list = QListWidget()
        self.results_list.currentItemChanged.connect(self.show_preview)
        self.results_list.setMinimumWidth(250)

        self.preview_label = QLabel("Preview will appear here")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.splitter.addWidget(self.results_list)
        self.splitter.addWidget(self.preview_label)
        self.splitter.setSizes([300, 800])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setMinimumHeight(300)

        # Debug row
        debug_row = QHBoxLayout()
        self.reopen_btn = QPushButton("See questionnaire")
        self.debug_btn = QPushButton("Show Last Debug Info")
        self.reopen_btn.clicked.connect(self.toggle_mode)
        self.debug_btn.clicked.connect(self.show_last_debug)
        debug_row.addStretch()
        debug_row.addWidget(self.reopen_btn)
        debug_row.addWidget(self.debug_btn)

        # Compose main layout
        layout.addWidget(self.top_widget)
        layout.addWidget(self.active_filters_label)
        layout.addLayout(controls_row)
        layout.addWidget(self.splitter, stretch=1)
        layout.addLayout(debug_row)
        self.setLayout(layout)

        # connect toggle
        self.code_radio.toggled.connect(self.toggle_mode)

        # last debug info store
        self.last_debug = None

        # After animation, enforce splitter sizes to avoid collapse
        self.height_anim.finished.connect(self.enforce_splitter_sizes)

    # ---------- helpers / actions ----------
    def enforce_splitter_sizes(self):
        total_w = max(self.width(), 1)
        left = max(250, int(total_w * 0.22))
        right = max(400, total_w - left)
        self.splitter.setSizes([left, right])

    def master_clear_all(self):
        """Clears questionnaire filters and code input."""
        # Questionnaire
        self.material_cb.setCurrentIndex(0)
        self.height_cb.setCurrentIndex(0)
        self.width_input.clear()
        self.color_cb.setCurrentIndex(0)
        for cb_list in self.design_checkboxes.values():
            for cb in cb_list:
                cb.setChecked(False)
        # Code
        self.search_input.clear()
        # UI feedback
        self.active_filters_label.setText("No filters applied")
        QMessageBox.information(self, "Cleared", "All inputs have been cleared.")

    def toggle_mode(self):
        if self.code_radio.isChecked():
            self.stack.setCurrentIndex(0)
            self.animate_height(HEIGHT_SEARCH)
        else:
            self.stack.setCurrentIndex(1)
            avail = self.parent().height() if self.parent() else self.height()
            min_results_area = 300
            max_top = max(HEIGHT_COLLAPSED_QN, avail - min_results_area)
            target = min(HEIGHT_QN, max_top)
            self.animate_height(target)

    def animate_height(self, target_height):
        self.height_anim.stop()
        self.height_anim.setStartValue(self.top_widget.maximumHeight())
        self.height_anim.setEndValue(target_height)
        self.height_anim.start()

    def search_clicked(self):
        """Shared Search button for both modes."""
        if self.code_radio.isChecked():
            self.do_search_code()
        else:
            self.do_search_qn()

    def do_search_code(self):
        code = self.search_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Please enter a product code.")
            return

        root_dir = self.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QMessageBox.critical(self, "Error", "Root folder is not set or no longer exists.")
            return

        self.active_filters_label.setText(f"Product code: {code}")

        results = search_files(root_dir, code)
        self.populate_results(results)

        dbg, _ = debug_search_files(root_dir, code)
        self.last_debug = dbg

        if not results:
            QMessageBox.information(self, "No Results", "No matching files found.")

    def do_search_qn(self):
        # collapse the questionnaire, buttons stay visible
        self.animate_height(HEIGHT_COLLAPSED_QN)

        parts = []

        # Material
        if self.material_cb.currentText():
            mat_name = self.material_cb.currentText()
            parts.append(MATERIAL_MAP[mat_name])

        # Designs
        selected_design_codes = []
        selected_designs_names = []
        for cat, cbs in self.design_checkboxes.items():
            for cb in cbs:
                if cb.isChecked():
                    name = cb.text().strip()
                    selected_designs_names.append(name)
                    if name in DESIGN_MAP:
                        selected_design_codes.append(DESIGN_MAP[name])
                    else:
                        print(f"[WARN] Design '{name}' not in DESIGN_MAP")

        # Height/Width -> size token
        height_val = self.height_cb.currentText().strip()
        width_val = self.width_input.text().strip()
        if height_val and not height_val.upper().endswith('F'):
            height_val = f'{height_val}F'

        size_text = ""
        if height_val and width_val:
            size_text = f'{width_val}"{height_val}'
        elif width_val:
            size_text = f'{width_val}"'
        elif height_val:
            size_text = height_val

        if size_text:
            parts.append(normalize_size_token(size_text))

        # EQ merge with L-count inside size
        if any(dc == "EQ" for dc in selected_design_codes) and size_text:
            m = re.search(r'(\d+)\s*[lL]\b', size_text)
            if m:
                eq_token = "EQ" + m.group(1) + "L"
                selected_design_codes = [dc for dc in selected_design_codes if dc != "EQ"]
                selected_design_codes.append(eq_token)

        # Append designs
        if selected_design_codes:
            parts.extend(selected_design_codes)

        # Colour
        if self.color_cb.currentText():
            parts.append(COLOR_MAP[self.color_cb.currentText()])

        # Build active filter summary (for UI label)
        summary_parts = []
        if self.material_cb.currentText():
            summary_parts.append(f"Material: {self.material_cb.currentText()}")
        if height_val:
            summary_parts.append(f"Height: {height_val}")
        if width_val:
            summary_parts.append(f"Width: {width_val} inches")
        if self.color_cb.currentText():
            summary_parts.append(f"Colour: {self.color_cb.currentText()}")
        if selected_designs_names:
            summary_parts.append("Designs: " + ", ".join(selected_designs_names))
        self.active_filters_label.setText(" | ".join(summary_parts) if summary_parts else "No filters applied")

        # Build code and run
        code = "_".join(parts)
        if not code:
            QMessageBox.warning(self, "Error", "Please fill at least one field.")
            return

        root_dir = self.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QMessageBox.critical(self, "Error", "Root folder is not set or no longer exists.")
            return

        results = search_files(root_dir, code)
        self.populate_results(results)

        dbg, _ = debug_search_files(root_dir, code)
        self.last_debug = dbg

        if not results:
            QMessageBox.information(self, "No Results", "No matching files found.")

    def populate_results(self, results):
        self.results_list.clear()
        if not results:
            return
        for p in results:
            parts = p.split(os.sep)
            if len(parts) > 4:
                display_text = os.path.join(*parts[4:])
            else:
                display_text = os.path.basename(p)
            self.results_list.addItem(display_text)
            self.results_list.item(self.results_list.count() - 1).setData(Qt.UserRole, p)

    def show_preview(self, current, _):
        if current:
            path = current.data(Qt.UserRole) or current.text()
            try:
                img = Image.open(path)
                qt_img = ImageQt.ImageQt(img)
                pixmap = QPixmap.fromImage(qt_img)
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width(),
                    self.preview_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            except Exception as e:
                self.preview_label.setText(f"Error loading image: {e}")

    def show_last_debug(self):
        if not self.last_debug:
            QMessageBox.information(self, "Debug", "No debug info available yet. Run a search first.")
            return
        dlg = DebugDialog(self.last_debug)
        dlg.exec()

    def get_root_dir(self):
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        if isinstance(parent, QMainWindow):
            return getattr(parent, "root_dir", None)
        return None

    def add_selected_to_cart(self):
        current = self.results_list.currentItem()
        if not current:
            QMessageBox.information(self, "Add to Cart", "No item selected.")
            return
        full_path = current.data(Qt.UserRole) or current.text()
        main_window = self.parent()
        while main_window and not isinstance(main_window, QMainWindow):
            main_window = main_window.parent()
        if main_window:
            tabs = main_window.findChild(QTabWidget)
            if tabs:
                for i in range(tabs.count()):
                    widget = tabs.widget(i)
                    if isinstance(widget, CartTab):
                        widget.add_to_cart(full_path)
                        QMessageBox.information(self, "Add to Cart", "Item added to cart.")
                        return
        QMessageBox.warning(self, "Add to Cart", "Cart tab not found.")

# Cart tab 
class CartTab(QWidget):
    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = root_dir
        self.cart_items = set()

        layout = QVBoxLayout()

        title = QLabel("Shopping Cart")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 18px;")
        layout.addWidget(title)

        # Splitter for list + preview
        self.splitter = QSplitter(Qt.Horizontal)
        self.cart_list = QListWidget()
        self.cart_list.setMinimumWidth(250)
        self.cart_list.currentItemChanged.connect(self.show_preview)

        # Right panel (image + path)
        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel("Preview will appear here")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        rp_layout.addWidget(self.preview_label)
        rp_layout.addWidget(self.path_label)
        rp_layout.addStretch()

        self.splitter.addWidget(self.cart_list)
        self.splitter.addWidget(right_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        layout.addWidget(self.splitter, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("Clear Cart")
        self.clear_btn.clicked.connect(self.clear_cart)
        self.checkout_btn = QPushButton("Checkout")
        self.checkout_btn.clicked.connect(self.checkout)

        btn_row.addStretch()
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.checkout_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def add_to_cart(self, item_path):
        if item_path not in self.cart_items:
            self.cart_items.add(item_path)
            display_text = os.path.basename(item_path)
            lw_item = QListWidgetItem(display_text)
            lw_item.setData(Qt.UserRole, item_path)
            self.cart_list.addItem(lw_item)

    def remove_selected(self):
        for item in self.cart_list.selectedItems():
            path = item.data(Qt.UserRole)
            self.cart_items.discard(path)
            self.cart_list.takeItem(self.cart_list.row(item))
        # Clear preview if nothing selected
        if self.cart_list.currentItem() is None:
            self.preview_label.clear()
            self.path_label.clear()

    def clear_cart(self):
        self.cart_items.clear()
        self.cart_list.clear()
        self.preview_label.clear()
        self.path_label.clear()

    def checkout(self):
        if not self.cart_items:
            QMessageBox.information(self, "Checkout", "Your cart is empty.")
            return
        QMessageBox.information(self, "Checkout", f"Checked out {len(self.cart_items)} item(s).")

    def show_preview(self, current, _):
        if current:
            path = current.data(Qt.UserRole)
            self.path_label.setText(path or "")
            try:
                img = Image.open(path)
                qt_img = ImageQt.ImageQt(img)
                pixmap = QPixmap.fromImage(qt_img)
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width(),
                    self.preview_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            except Exception as e:
                self.preview_label.setText(f"Error loading image: {e}")

class MainWindow(QMainWindow):
    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = root_dir
        self.setWindowTitle("Naturo Surfaces Search (Beta)")

        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(900, 600)
        self.setMaximumSize(screen.width(), screen.height())
        w = min(1100, screen.width())
        h = min(750, screen.height())
        self.resize(w, h)

        tabs = QTabWidget()
        tabs.addTab(SearchTab(root_dir), "Search")
        tabs.addTab(CartTab(root_dir), "Cart")
        # tabs.tabBar().hide()  # keep hidden if you want a kiosk-like UI
        self.setCentralWidget(tabs)

        self.setStyleSheet("QMainWindow { background-color: #449950; }")

# ---------------- bootstrap ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    cfg = load_config()
    root_dir = cfg.get("root_dir")
    if not root_dir or not os.path.exists(root_dir):
        root_dir = pick_root_dir()
        if not root_dir:
            print("No folder selected. Exiting.")
            sys.exit(0)
        cfg["root_dir"] = root_dir
        save_config(cfg)
    win = MainWindow(root_dir)
    win.show()
    sys.exit(app.exec())
