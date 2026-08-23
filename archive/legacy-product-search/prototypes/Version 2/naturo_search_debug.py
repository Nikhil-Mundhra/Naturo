# Naturo Surfaces App - Debuggable PySide6 Version
# pip install PySide6 pillow
# python naturo_search_debug.py

import sys, os, re, json
from PIL import Image, ImageQt
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLineEdit, QPushButton, QLabel, QListWidget, QComboBox, QFormLayout,
    QStackedWidget, QSplitter, QMessageBox, QFileDialog, QRadioButton,
    QButtonGroup, QSizePolicy, QListWidgetItem, QDialog, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap

# ---------------- CONFIG ----------------
CONFIG_FILE = "naturo_config.json"
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

COLOR_MAP = {
    "Red": "RD", "Black": "BL", "Gold": "GD", "Silver": "SV", "Teak": "TK",
    "Walnut": "WL", "Yellow": "YL", "Blue": "BU", "Steel": "ST", "Grey": "GY",
    "Brown": "BR", "White": "WT", "Purple": "PL", "Green": "GN", "Rose Gold": "RG",
    "Beage": "BG", "Cream": "CR", "Mobe": "MO", "Metalic": "MT", "Marble": "MB"
}

MATERIAL_MAP = {
    "Char Coal": "CH",
    "PVC": "PV",
    "WPC": "WP",
    "Super Heavy": "SPHV",
    "Ultra Voilet Foarm Sheet": "UVFS",
    "Ultra Voilet Marble Sheet": "UVMB",
    "Tiger Febric": "TG",
    "Acrylic": "ACY"
}

DESIGN_MAP = {
    'Inch': '"',
    "Foot": "F",
    "Flutted": "FT",
    "Equal Distance Between The Lines": "EQ",
    "Line": "L",
    "Step": "S",
    "Double Tone": "DT",
    "Texture": "TX",
    "Digital Marble Sheet": "DMS",
    "Flutted Marble Sheet": "FMS",
    "Book Match Digital Marble": "BMDM",
    "Slim": "SL",
    "Panel No Line": "PL",
    "Wooden": "WD",
    "Digital Marble Gold Line": "DMGL",
    "High/3D Sheet": "H3D",
    "Seamless": "SL",
    "Matt": "MTT",
    "Louver": "LV",
    "Printed": "PR",
    "Round": "RD",
    "Volume": "VO",
    "Catlogue": "CT"
}

# ---------------- UTILS ----------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

def pick_root_dir(parent=None):
    dlg = QFileDialog(parent)
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
    # normalize filename to a searchable form: lowercase, non-alnum -> underscore
    return re.sub(r'[^0-9A-Za-z_]+', '_', name).lower()

def normalize_size_token(s):
    # normalize various forms of sizes: 12"9.5F -> 12_9_5f or 12_9.5f
    if not s: return s
    x = s.replace('"', '_').replace('.', '_').replace(' ', '_')
    x = re.sub(r'__+', '_', x)
    return x.lower()

# ---------------- PARSING ----------------
def tokenize_input(code):
    if not code: return []
    s = re.sub(r'[^0-9A-Za-z_"]+', '_', code)
    s = re.sub(r'__+', '_', s)
    return [t for t in s.split('_') if t]

def parse_product_code(code):
    tokens = tokenize_input(code)
    tokens_lc = [t.lower().replace('"', '_') for t in tokens]
    # materials/colors are the short codes (pv, ch, etc)
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
    # required_colors are short codes like 'bl','br'
    for col in required_colors:
        # boundary-aware
        if re.search(r'(^|_)' + re.escape(col) + r'(_|$)', searchable):
            return True
        # allow direct attachment (pvbl, blcst etc)
        if col in searchable:
            return True
    return False

def matches_size(searchable, required_sizes):
    for sz in required_sizes:
        v1 = sz.lower()
        v2 = v1.replace('_','')
        v3 = v1.rstrip('f').rstrip('l')
        for v in (v1, v2, v3):
            if v and v in searchable:
                return True
    return False

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
        content.append(f"Matching files found: {debug_info['matches_count']} (showing up to 40)")
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
        self.last_debug = None
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

        # Stacked widget for modes
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
        form = QFormLayout()
        self.material_cb = QComboBox()
        self.material_cb.addItems([""] + list(MATERIAL_MAP.keys()))
        # multi-select design list
        self.design_list = QListWidget()
        self.design_list.setSelectionMode(QListWidget.MultiSelection)
        for k in DESIGN_MAP.keys():
            item = QListWidgetItem(k)
            self.design_list.addItem(item)
        self.size_input = QLineEdit()
        self.color_cb = QComboBox()
        self.color_cb.addItems([""] + list(COLOR_MAP.keys()))
        self.supplier_input = QLineEdit()
        self.foldercode_input = QLineEdit()
        form.addRow("Material:", self.material_cb)
        form.addRow("Design(s):", self.design_list)
        form.addRow("Size (e.g., 12\"9.5F or 14L):", self.size_input)
        form.addRow("Colour:", self.color_cb)
        form.addRow("Supplier Code (e.g., KYGH):", self.supplier_input)
        form.addRow("Folder Code (e.g., 02):", self.foldercode_input)
        self.search_btn_qn = QPushButton("Search")
        self.search_btn_qn.clicked.connect(self.do_search_qn)
        form.addRow(self.search_btn_qn)
        qn_widget.setLayout(form)

        self.stack.addWidget(code_widget)
        self.stack.addWidget(qn_widget)

        # Top panel with animation
        self.top_widget = QWidget()
        top_panel = QVBoxLayout()
        top_panel.addLayout(toggle_row)
        top_panel.addWidget(self.stack)
        # debug checkbox and show button
        debug_row = QHBoxLayout()
        self.debug_checkbox = QCheckBox("Auto-show debug on no results")
        self.debug_button = QPushButton("Show Last Debug Info")
        self.debug_button.clicked.connect(self.show_last_debug)
        debug_row.addWidget(self.debug_checkbox)
        debug_row.addWidget(self.debug_button)
        top_panel.addLayout(debug_row)
        self.top_widget.setLayout(top_panel)
        self.top_widget.setMaximumHeight(130)  # start in code mode

        self.height_anim = QPropertyAnimation(self.top_widget, b"maximumHeight")
        self.height_anim.setDuration(300)

        # Results & preview
        splitter = QSplitter(Qt.Horizontal)
        self.results_list = QListWidget()
        self.results_list.currentItemChanged.connect(self.show_preview)
        self.preview_label = QLabel("Preview will appear here")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.results_list)
        splitter.addWidget(self.preview_label)
        splitter.setSizes([300, 800])

        layout.addWidget(self.top_widget)
        layout.addWidget(splitter, stretch=1)
        self.setLayout(layout)

        self.code_radio.toggled.connect(self.toggle_mode)

    def toggle_mode(self):
        if self.code_radio.isChecked():
            self.stack.setCurrentIndex(0)
            self.animate_height(150)
        else:
            self.stack.setCurrentIndex(1)
            self.animate_height(450)

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
        debug, matches = debug_search_files(self.root_dir, code)
        self.last_debug = debug
        self.populate_results(matches)
        if not matches and self.debug_checkbox.isChecked():
            self.show_last_debug()

    def do_search_qn(self):
        parts = []
        # material code
        if self.material_cb.currentText():
            parts.append(MATERIAL_MAP[self.material_cb.currentText()])
        # designs (multiple)
        selected_designs = [item.text() for item in self.design_list.selectedItems()]
        design_codes = [DESIGN_MAP[d] for d in selected_designs if d in DESIGN_MAP]
        # size text - may be like '14L' or '12"9.5F'
        size_text = self.size_input.text().strip()
        size_norm = normalize_size_token(size_text) if size_text else ""
        # handle EQ + lines merging: if EQ selected and size_text looks like '14L' or contains digits+L
        if "Equal Distance Between The Lines" in selected_designs:
            m = re.search(r'(\\d+)\\s*[lL]\\b', size_text)
            if m:
                eq_token = "EQ" + m.group(1) + "L"
                design_codes = [dc for dc in design_codes if dc != "EQ"]
                design_codes.append(eq_token)
                size_norm = re.sub(r'\\d+\\s*[lL]\\b', '', size_norm)
                size_norm = size_norm.strip('_')
        # append design codes in order
        for dc in design_codes:
            parts.append(dc)
        # append size if present (normalize)
        if size_norm:
            parts.append(size_norm)
        # colour
        if self.color_cb.currentText():
            parts.append(COLOR_MAP[self.color_cb.currentText()])
        # folder and supplier
        if self.foldercode_input.text():
            parts.append(self.foldercode_input.text().strip())
        if self.supplier_input.text():
            parts.append(self.supplier_input.text().strip())

        code = "_".join(parts)
        if not code:
            QMessageBox.warning(self, "Error", "Please fill at least one field.")
            return
        debug, matches = debug_search_files(self.root_dir, code)
        self.last_debug = debug
        self.populate_results(matches)
        if not matches and self.debug_checkbox.isChecked():
            self.show_last_debug()

    def populate_results(self, results):
        self.results_list.clear()
        if not results:
            QMessageBox.information(self, "No Results", "No matching files found.")
            return
        for p in results:
            self.results_list.addItem(p)

    def show_last_debug(self):
        if not self.last_debug:
            QMessageBox.information(self, "Debug", "No debug info available yet. Run a search first.")
            return
        dlg = DebugDialog(self.last_debug)
        dlg.exec()

    def show_preview(self, current, _):
        if current:
            path = current.text()
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
        self.setWindowTitle("Naturo Surfaces Search - Debug")
        self.resize(1200, 800)
        tabs = QTabWidget()
        tabs.addTab(SearchTab(root_dir), "Search")
        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    cfg = load_config()
    root_dir = cfg.get("root_dir")
    if not root_dir or not os.path.exists(root_dir):
        root_dir = pick_root_dir(None)
        if not root_dir:
            print("No folder selected. Exiting.")
            sys.exit(0)
        cfg["root_dir"] = root_dir
        save_config(cfg)
    win = MainWindow(root_dir)
    win.show()
    sys.exit(app.exec())
