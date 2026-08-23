# naturo_search_final.py
# Naturo Surfaces App - PySide6 (merged collapsible design selector + debug)
# alias python=python3
# brew install PySide6 pillow
# python naturo_search_final.py
# eg: 24_PK_PV_BR_MRP_975_FT_Pr_Eq_14L_12"9.5F_02_KYGH_Q8
''' For example the code: 63_PK_PV_BL_MRP_975_FT_Pr_Eq14L 12"9.5F_02_KYGH_Q8,
 should result in /KYGH_Kiyaan, Ganour /KYGH Selected Item/
 P_02_FT_Pr_APR 25_12_9.5F_PV_KYGH/P_PV_FT Pr Eq14L 12_9.5F_02_KYGH_Q8.jpg '''

import sys
import os
import re
import json
from PIL import Image, ImageQt
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLineEdit, QPushButton, QLabel, QListWidget, QComboBox, QFormLayout,
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
    files = []
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

def parse_product_code(code):
    tokens = normalize_input(code)
    tokens_lc = [t.lower().replace('"', '_') for t in tokens]
    material_codes = [v.lower() for v in MATERIAL_MAP.values()]
    color_codes = [v.lower() for v in COLOR_MAP.values()]
    material = [t for t in tokens_lc if t in material_codes]
    color = [t for t in tokens_lc if t in color_codes]
    supplier = tokens[-2] if len(tokens) >= 2 else None
    folder_code = tokens[-3] if len(tokens) >= 3 else None
    size = []
    for t in tokens:
        tl = t.lower()
        norm = re.sub(r'["\.]', '_', tl)
        norm = re.sub(r'[^0-9a-z_]+', '_', norm)
        norm = re.sub(r'__+', '_', norm)
        if re.search(r'\d', norm) and ('f' in norm or 'l' in norm):
            size.append(norm)
    size_canonical = list({normalize_size_token(s) for s in size})
    return {
        "tokens": tokens,
        "material": material,
        "color": color,
        "size": size_canonical,
        "supplier": supplier.lower() if supplier else None,
        "folder_code": folder_code.lower() if folder_code else None
    }

# ---------------- SEARCH HELPERS ----------------
def build_dir_index(root_dir):
    return {d for d, _, _ in os.walk(root_dir)}

def find_supplier_selected_folder(root_dir, supplier_code):
    if not supplier_code:
        return None
    sc = supplier_code.lower()
    candidates = [d for d in build_dir_index(root_dir) if sc in os.path.basename(d).lower()]
    for c in candidates:
        for root, dirs, _ in os.walk(c):
            for sub in dirs:
                if 'selected' in sub.lower():
                    return os.path.join(root, sub)
    return candidates[0] if candidates else None

def find_folder_with_code(parent_dir, folder_code):
    if not parent_dir or not folder_code:
        return None
    fc = folder_code.lower()
    for root, dirs, _ in os.walk(parent_dir):
        for d in dirs:
            searchable = re.sub(r'[^0-9a-z]+', '_', d.lower())
            if re.search(r'(^|_)' + re.escape(fc) + r'(_|$)', searchable):
                return os.path.join(root, d)
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
    parsed = parse_product_code(code)
    supplier = parsed["supplier"]
    folder_code = parsed["folder_code"]
    required_materials = parsed["material"]
    required_colors = parsed["color"]
    required_sizes = parsed["size"]

    search_root = root_dir
    if supplier:
        sup_folder = find_supplier_selected_folder(root_dir, supplier)
        if sup_folder:
            fc_folder = find_folder_with_code(sup_folder, folder_code) if folder_code else None
            search_root = fc_folder or sup_folder

    candidate_files = scan_images(search_root)
    results = []
    for p in candidate_files:
        s = make_searchable(os.path.basename(p))
        if required_materials and not any(mat in s for mat in required_materials):
            continue
        if required_colors and not color_matches(s, required_colors):
            continue
        if required_sizes and not matches_size(s, required_sizes):
            continue
        results.append(p)
    return results

def debug_search_files(root_dir, code, max_show=40):
    parsed = parse_product_code(code)
    supplier = parsed["supplier"]
    folder_code = parsed["folder_code"]
    required_materials = parsed["material"]
    required_colors = parsed["color"]
    required_sizes = parsed["size"]

    search_root = root_dir
    sup_folder = None
    fc_folder = None
    if supplier:
        sup_folder = find_supplier_selected_folder(root_dir, supplier)
        if sup_folder:
            fc_folder = find_folder_with_code(sup_folder, folder_code) if folder_code else None
            search_root = fc_folder or sup_folder

    candidate_files = scan_images(search_root)
    reasons = []
    matches = []
    for p in candidate_files:
        s = make_searchable(os.path.basename(p))
        fail_reasons = []
        if required_materials and not any(mat in s for mat in required_materials):
            fail_reasons.append("material")
        if required_colors and not color_matches(s, required_colors):
            fail_reasons.append("color")
        if required_sizes and not matches_size(s, required_sizes):
            fail_reasons.append("size")
        if not fail_reasons:
            matches.append(p)
        else:
            reasons.append((p, fail_reasons))
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

        # Toggle buttons
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
        self.search_btn_code = QPushButton("Search")
        self.search_btn_code.clicked.connect(self.do_search_code)
        code_layout.addWidget(self.search_btn_code)
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

            # Select / Clear row
            row = QHBoxLayout()
            select_all_btn = QPushButton("Select All")
            clear_all_btn = QPushButton("Clear All")
            row.addWidget(select_all_btn)
            row.addWidget(clear_all_btn)
            vbox.addLayout(row)

            cb_list = []
            for name in designs.keys():
                cb = QCheckBox(name)
                vbox.addWidget(cb)
                cb_list.append(cb)

            select_all_btn.clicked.connect(lambda _, l=cb_list: [c.setChecked(True) for c in l])
            clear_all_btn.clicked.connect(lambda _, l=cb_list: [c.setChecked(False) for c in l])

            vbox.addStretch()
            scroll.setWidget(container)
            self.design_toolbox.addItem(scroll, cat)
            self.design_checkboxes[cat] = cb_list

        right_widget = self.design_toolbox

        # ===== TOP HORIZONTAL SPLIT =====
        top_cols = QHBoxLayout()
        top_cols.addWidget(left_widget, 1)
        top_cols.addWidget(right_widget, 2)

        # ===== SEARCH + MASTER CLEAR ALL =====
        self.search_btn_qn = QPushButton("Search")
        self.search_btn_qn.clicked.connect(self.do_search_qn)

        self.clear_all_btn_master = QPushButton("Clear All")
        self.clear_all_btn_master.clicked.connect(self.master_clear_all)

        search_row = QHBoxLayout()
        search_row.addStretch()
        search_row.addWidget(self.search_btn_qn)
        search_row.addWidget(self.clear_all_btn_master)
        search_row.addStretch()

        # ===== MAIN VERTICAL STACK =====
        main_vbox = QVBoxLayout()
        main_vbox.addLayout(top_cols)
        main_vbox.addLayout(search_row)

        qn_widget.setLayout(main_vbox)

        self.stack.addWidget(code_widget)
        self.stack.addWidget(qn_widget)

        # Top widget with animation
        self.top_widget = QWidget()
        top_panel = QVBoxLayout()
        top_panel.addLayout(toggle_row)
        top_panel.addWidget(self.stack)
        self.top_widget.setLayout(top_panel)
        self.top_widget.setMaximumHeight(HEIGHT_SEARCH)
        self.top_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.height_anim = QPropertyAnimation(self.top_widget, b"maximumHeight")
        self.height_anim.setDuration(300)

        # Results & preview
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

        # Debug button (keeps debug capability)
        debug_row = QHBoxLayout()
        self.reopen_btn = QPushButton("Go back to questionnaire")
        self.debug_btn = QPushButton("Show Last Debug Info")
        self.reopen_btn.clicked.connect(self.toggle_mode)
        self.debug_btn.clicked.connect(self.show_last_debug)
        debug_row.addStretch()
        debug_row.addWidget(self.reopen_btn)
        debug_row.addWidget(self.debug_btn)

        layout.addWidget(self.top_widget)
        layout.addWidget(self.splitter, stretch=1)
        layout.addLayout(debug_row)
        self.setLayout(layout)

        # connect toggle
        self.code_radio.toggled.connect(self.toggle_mode)

        # last debug info store
        self.last_debug = None

        # After animation, enforce splitter sizes to avoid collapse
        self.height_anim.finished.connect(self.enforce_splitter_sizes)

    def enforce_splitter_sizes(self):
        total_w = max(self.width(), 1)
        left = max(250, int(total_w * 0.22))
        right = max(400, total_w - left)
        self.splitter.setSizes([left, right])

    def master_clear_all(self):
        """Clears all questionnaire filters."""
        # Reset Material, Height, Width, Colour
        self.material_cb.setCurrentIndex(0)
        self.height_cb.setCurrentIndex(0)
        self.width_input.clear()
        self.color_cb.setCurrentIndex(0)

        # Uncheck all designs
        for cb_list in self.design_checkboxes.values():
            for cb in cb_list:
                cb.setChecked(False)

        QMessageBox.information(self, "Cleared", "All filters have been cleared.")

    def toggle_mode(self):
        if self.code_radio.isChecked():
            self.stack.setCurrentIndex(0)
            self.animate_height(HEIGHT_SEARCH)
        else:
            self.stack.setCurrentIndex(1)
            # Clamp QN to not starve the splitter area
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

    def do_search_code(self):
        code = self.search_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Please enter a product code.")
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

    def do_search_qn(self):
        self.animate_height(HEIGHT_COLLAPSED_QN)  # Collapses the questionnaire
        parts = []

        # Material
        if self.material_cb.currentText():
            mat_name = self.material_cb.currentText()
            parts.append(MATERIAL_MAP[mat_name])

        # Collect selected design codes from all categories
        selected_design_codes = []
        for cat, cbs in self.design_checkboxes.items():
            for cb in cbs:
                if cb.isChecked():
                    name = cb.text().strip()
                    if name in DESIGN_MAP:
                        selected_design_codes.append(DESIGN_MAP[name])
                    else:
                        print(f"[WARN] Design '{name}' not in DESIGN_MAP")

        # Height & Width handling, size / dimensions
        height_val = self.height_cb.currentText().strip()
        width_val = self.width_input.text().strip()

        if height_val:
            if not height_val.upper().endswith('F'):
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

        if any(dc == "EQ" for dc in selected_design_codes) and size_text:
            m = re.search(r'(\d+)\s*[lL]\b', size_text)
            if m:
                eq_token = "EQ" + m.group(1) + "L"
                selected_design_codes = [dc for dc in selected_design_codes if dc != "EQ"]
                selected_design_codes.append(eq_token)
                size_text = re.sub(r'\d+\s*[lL]\b', '', size_text).strip('_ ')

        if selected_design_codes:
            parts.extend(selected_design_codes)

        # Color
        if self.color_cb.currentText():
            parts.append(COLOR_MAP[self.color_cb.currentText()])

        code = "_".join(parts)
        if not code:
            QMessageBox.warning(self, "Error", "Please fill at least one field.")
            return

        results = search_files(self.get_root_dir(), code)
        self.populate_results(results)

        dbg, _ = debug_search_files(self.get_root_dir(), code)
        self.last_debug = dbg

        if not results:
            QMessageBox.information(self, "No Results", "No matching files found.")

    def populate_results(self, results):
        import os
        self.results_list.clear()
        if not results:
            return
        for p in results:
            parts = p.split(os.sep)
            if len(parts) > 4:
                display_text = os.path.join(*parts[4:])  # remove first 4 dirs for display
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
        tabs.addTab(SearchTab(root_dir), "")
        tabs.tabBar().hide()
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
