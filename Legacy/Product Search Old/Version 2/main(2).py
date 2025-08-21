# Naturo Surfaces App - PySide6 with Either-Or Search (Code or Questionnaire)
# pip install PySide6 pillow
# python naturo_search.py

import sys, os, re, json
from PIL import Image, ImageQt
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLineEdit, QPushButton, QLabel, QListWidget, QComboBox, QTextEdit,
    QFormLayout, QStackedWidget, QSplitter, QMessageBox, QFileDialog,
    QRadioButton, QButtonGroup, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

# ---------------- CONFIG ----------------
CONFIG_FILE = "naturo_config.json"
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

MATERIAL_CODES = {
    'ch','pv','wp','ft','eq','l','s','dt','tx','dms','fms','bmdm','sl','sphv',
    'uvfs','uvmb','pl','wd','dmgl','h3d','mtt','lv','pr','rd','acy'
}
COLOR_CODES = {
    'rd','bl','gd','tk','wl','yl','st','gy','br','pl','gn','rg','bg','cr','mo','mt','mb','wt','sv','bk'
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

# ---------------- PARSING ----------------
def normalize_input(code):
    s = re.sub(r'[^0-9A-Za-z_"]+', '_', code)
    s = re.sub(r'__+', '_', s)
    return [t for t in s.split('_') if t]

def parse_product_code(code):
    tokens = normalize_input(code)
    tokens_lc = [t.lower().replace('"', '_') for t in tokens]
    material = [t for t in tokens_lc if t in MATERIAL_CODES]
    color = [t for t in tokens_lc if t in COLOR_CODES]

    supplier = None
    folder_code = None
    if len(tokens) >= 4:
        supplier = tokens[-2]
        folder_code = tokens[-3]

    size = []
    for t in tokens:
        tl = t.lower()
        norm = re.sub(r'["\.]', '_', tl)
        norm = re.sub(r'[^0-9a-z_]+', '_', norm)
        norm = re.sub(r'__+', '_', norm)
        if re.search(r'\d+_?\d*.*f', norm) or ('f' in norm and re.search(r'\d', norm)):
            size.append(norm)
    size_canonical = list({re.sub(r'__+', '_', s).lower() for s in size})

    return {
        "tokens": [t.lower() for t in tokens],
        "material": list(dict.fromkeys(material)),
        "color": list(dict.fromkeys(color)),
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

def matches_size(searchable, required_sizes):
    for sz in required_sizes:
        variants = {sz, sz.replace('_',''), sz.rstrip('f')}
        for v in variants:
            if v and v in searchable:
                return True
    return False

def search_files(root_dir, code):
    parsed = parse_product_code(code)
    required_materials = parsed["material"]
    required_colors = parsed["color"]
    required_sizes = parsed["size"]
    supplier = parsed["supplier"]
    folder_code = parsed["folder_code"]

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
        if required_colors and not any(col in s for col in required_colors):
            continue
        if required_sizes and not matches_size(s, required_sizes):
            continue
        results.append(p)
    return results

# ---------------- UI ----------------
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
        layout.addLayout(toggle_row)

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
        self.material_cb.addItems(["", "PVC", "WPC", "Flutted"])
        self.design_cb = QComboBox()
        self.design_cb.addItems(["", "Pr", "Eq", "Tx"])
        self.size_input = QLineEdit()
        self.color_cb = QComboBox()
        self.color_cb.addItems(["", "BR", "BL", "RD", "GD"])
        self.supplier_input = QLineEdit()
        self.foldercode_input = QLineEdit()
        form.addRow("Material:", self.material_cb)
        form.addRow("Design Type:", self.design_cb)
        form.addRow("Size:", self.size_input)
        form.addRow("Colour:", self.color_cb)
        form.addRow("Supplier Code:", self.supplier_input)
        form.addRow("Folder Code:", self.foldercode_input)
        self.search_btn_qn = QPushButton("Search")
        self.search_btn_qn.clicked.connect(self.do_search_qn)
        form.addRow(self.search_btn_qn)
        qn_widget.setLayout(form)

        self.stack.addWidget(code_widget)
        self.stack.addWidget(qn_widget)
        layout.addWidget(self.stack)

        # Results & preview
        splitter = QSplitter(Qt.Horizontal)
        self.results_list = QListWidget()
        self.results_list.currentItemChanged.connect(self.show_preview)
        self.preview_label = QLabel("Preview will appear here")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.results_list)
        splitter.addWidget(self.preview_label)
        splitter.setSizes([250, 600])
        layout.addWidget(splitter)

        self.setLayout(layout)
        self.code_radio.toggled.connect(self.toggle_mode)

    def toggle_mode(self):
        if self.code_radio.isChecked():
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)

    def do_search_code(self):
        code = self.search_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Please enter a product code.")
            return
        self.run_search(code)

    def do_search_qn(self):
        # Build pseudo-code
        parts = []
        if self.material_cb.currentText():
            parts.append(self.material_cb.currentText())
        if self.design_cb.currentText():
            parts.append(self.design_cb.currentText())
        if self.size_input.text():
            parts.append(self.size_input.text())
        if self.color_cb.currentText():
            parts.append(self.color_cb.currentText())
        if self.foldercode_input.text():
            parts.append(self.foldercode_input.text())
        if self.supplier_input.text():
            parts.append(self.supplier_input.text())
        code = "_".join(parts)
        if not code:
            QMessageBox.warning(self, "Error", "Please fill at least one field.")
            return
        self.run_search(code)

    def run_search(self, code):
        results = search_files(self.root_dir, code)
        self.results_list.clear()
        if not results:
            QMessageBox.information(self, "No Results", "No matching files found.")
            return
        for path in results:
            self.results_list.addItem(path)

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
        self.setWindowTitle("Naturo Surfaces Search")
        self.resize(1100, 750)
        tabs = QTabWidget()
        tabs.addTab(SearchTab(root_dir), "Search")
        self.setCentralWidget(tabs)

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
