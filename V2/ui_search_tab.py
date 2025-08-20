import os
from PIL import Image, ImageQt
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QLineEdit, QToolBox,
    QScrollArea, QCheckBox, QSizePolicy, QLabel, QPushButton, QStackedWidget,
    QRadioButton, QButtonGroup, QSplitter, QListWidget, QMessageBox, QListWidgetItem
)

from .constants import (
    MATERIAL_MAP, COLOR_MAP, DESIGN_CATEGORIES,
    HEIGHT_SEARCH, HEIGHT_QN, HEIGHT_COLLAPSED_QN
)
from .folder_index import FolderIndex
from .ui_debug import DebugDialog

class SearchTab(QWidget):
    def __init__(self, root_dir, index: FolderIndex):
        super().__init__()
        self.root_dir = root_dir
        self.index = index
        layout = QVBoxLayout()

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

        self.stack = QStackedWidget()

        code_widget = QWidget()
        code_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter full product code...")
        code_layout.addWidget(self.search_input)
        code_widget.setLayout(code_layout)

        qn_widget = QWidget()

        left_form = QFormLayout()

        self.material_cb = QComboBox()
        self.material_cb.addItems([""] + list(MATERIAL_MAP.keys()))
        left_form.addRow("Material:", self.material_cb)

        self.height_cb = QComboBox()
        self.height_cb.addItems(["", '8F', '9F', '9.5F'])
        left_form.addRow("Height:", self.height_cb)

        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText('Width in inches')
        left_form.addRow("Width:", self.width_input)

        self.color_cb = QComboBox()
        self.color_cb.addItems([""] + list(COLOR_MAP.keys()))
        left_form.addRow("Colour:", self.color_cb)

        left_widget = QWidget()
        left_widget.setLayout(left_form)

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

        top_cols = QHBoxLayout()
        top_cols.setContentsMargins(0, 0, 0, 0)
        top_cols.setSpacing(10)
        top_cols.addWidget(left_widget, 1)
        top_cols.addWidget(right_widget, 2)

        qn_main_vbox = QVBoxLayout()
        qn_main_vbox.setContentsMargins(0, 0, 0, 0)
        qn_main_vbox.setSpacing(5)
        qn_main_vbox.addLayout(top_cols)
        qn_widget.setLayout(qn_main_vbox)

        self.stack.addWidget(code_widget)
        self.stack.addWidget(qn_widget)

        self.top_widget = QWidget()
        top_panel = QVBoxLayout()
        top_panel.addLayout(toggle_row)
        top_panel.addWidget(self.stack)
        self.top_widget.setLayout(top_panel)
        self.top_widget.setMaximumHeight(HEIGHT_SEARCH)
        self.top_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.height_anim = QPropertyAnimation(self.top_widget, b"maximumHeight")
        self.height_anim.setDuration(300)

        self.active_filters_label = QLabel("")
        self.active_filters_label.setStyleSheet("font-weight: bold; padding: 6px;")

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

        debug_row = QHBoxLayout()
        self.reopen_btn = QPushButton("See questionnaire")
        self.debug_btn = QPushButton("Show Last Debug Info")
        self.refresh_cache_btn = QPushButton("Refresh Cache")
        self.reopen_btn.clicked.connect(self.toggle_mode)
        self.debug_btn.clicked.connect(self.show_last_debug)
        self.refresh_cache_btn.clicked.connect(self.refresh_cache)
        debug_row.addStretch()
        debug_row.addWidget(self.reopen_btn)
        debug_row.addWidget(self.debug_btn)
        debug_row.addWidget(self.refresh_cache_btn)

        layout.addWidget(self.top_widget)
        layout.addWidget(self.active_filters_label)
        layout.addLayout(controls_row)
        layout.addWidget(self.splitter, stretch=1)
        layout.addLayout(debug_row)
        self.setLayout(layout)

        self.code_radio.toggled.connect(self.toggle_mode)

        self.last_debug = None
        self.height_anim.finished.connect(self.enforce_splitter_sizes)

    def enforce_splitter_sizes(self):
        total_w = max(self.width(), 1)
        left = max(250, int(total_w * 0.22))
        right = max(400, total_w - left)
        self.splitter.setSizes([left, right])

    def master_clear_all(self):
        self.material_cb.setCurrentIndex(0)
        self.height_cb.setCurrentIndex(0)
        self.width_input.clear()
        self.color_cb.setCurrentIndex(0)
        for cb_list in self.design_checkboxes.values():
            for cb in cb_list:
                cb.setChecked(False)
        self.search_input.clear()
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
        if self.code_radio.isChecked():
            self.do_search_code()
        else:
            self.do_search_qn()

    def do_search_code(self):
        code = self.search_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Please enter a product code.")
            return

        self.active_filters_label.setText(f"Product code: {code}")

        # Single search call with debug info
        dbg, results = self.index.debug_search_files(code)
        self.last_debug = dbg
        self.populate_results(results)

        if not results:
            QMessageBox.information(self, "No Results", "No matching files found.")

    from .parsing import build_selection  # add near imports

    def do_search_qn(self):
        # Collapse the panel to free space
        self.animate_height(HEIGHT_COLLAPSED_QN)

        # Collect selections
        material = self.material_cb.currentText().strip() or None
        height = self.height_cb.currentText().strip() or None
        width_in = self.width_input.text().strip() or None
        color = self.color_cb.currentText().strip() or None

        # Collect selected designs across all categories
        designs = []
        for cat, cb_list in self.design_checkboxes.items():
            for cb in cb_list:
                if cb.isChecked():
                    designs.append(cb.text())

        # Build normalized selection
        selection = build_selection(
            material=material,
            height=height,
            width_inches=width_in,
            color=color,
            designs=designs,x
            supplier=None,        # optionally add a Supplier dropdown later
            folder_code=None,     # optionally add Folder Code input later
            file_token=None       # optionally add extra token input later
        )

        # Human-readable active filters label
        parts = []
        if material: parts.append(f"Material: {material}")
        if color: parts.append(f"Colour: {color}")
        if height: parts.append(f"Height: {height}")
        if width_in: parts.append(f"Width: {width_in} in")
        if designs: parts.append(f"Designs: {', '.join(designs)}")
        self.active_filters_label.setText(" | ".join(parts) if parts else "No filters applied")

        # Execute
        dbg, exact, suggestions = self.index.search_by_selection(selection)
        # Store debug for dialog
        self.last_debug = {
            "parsed": dbg.get("selection"),
            "initial_root": dbg.get("initial_root"),
            "supplier_folder_found": dbg.get("supplier_folder_found"),
            "folder_code_folder_found": dbg.get("folder_code_folder_found"),
            "autodescent_final_root": dbg.get("autodescent_final_root"),
            "autodescent_stop_reason": dbg.get("autodescent_stop_reason"),
            "candidate_count": dbg.get("candidate_count"),
            "matches_count": len(exact),
            "matches": exact[:60],
            "rejections": [(p, m) for (p, m, _sc) in dbg.get("sample_suggestions", [])],
        }

        # Populate UI list: exact first, then a separator, then suggestions
        self.results_list.clear()

        def add_items(paths, prefix=None):
            for p in paths:
                item = QListWidgetItem(os.path.basename(p))
                item.setData(Qt.UserRole, p)
                if prefix:
                    item.setText(f"{prefix} {item.text()}")
                self.results_list.addItem(item)

        if exact:
            add_items(exact)
        if suggestions:
            # separator
            sep = QListWidgetItem("—— Related suggestions ——")
            sep.setFlags(sep.flags() & ~Qt.ItemIsSelectable)
            self.results_list.addItem(sep)
            # show suggestions with a subtle tag and maybe the score missing count
            for (p, missing, sc) in suggestions:
                label = f"{os.path.basename(p)}  [score {sc}; missing: {','.join(missing)}]"
                it = QListWidgetItem(label)
                it.setData(Qt.UserRole, p)
                self.results_list.addItem(it)

        if not exact and not suggestions:
            QMessageBox.information(self, "No Results", "No matching files or suggestions found.")


    def populate_results(self, paths):
        self.results_list.clear()
        for p in paths:
            item = QListWidgetItem(os.path.basename(p))
            item.setData(Qt.UserRole, p)
            self.results_list.addItem(item)

    def show_preview(self, current, previous):
        if not current:
            self.preview_label.setText("Preview will appear here")
            self.preview_label.setPixmap(QPixmap())
            return
        p = current.data(Qt.UserRole)
        try:
            if p.lower().endswith(('.pdf',)):
                # Future-proof: Add PDF preview support later
                self.preview_label.setText("PDF preview not supported; open externally.")
                self.preview_label.setPixmap(QPixmap())
                return
            img = Image.open(p)
            qimg = ImageQt.ImageQt(img)
            pix = QPixmap.fromImage(qimg)
            if not pix.isNull():
                scaled = pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
            else:
                self.preview_label.setText("Cannot preview image.")
        except Exception:
            self.preview_label.setText("Cannot preview this file.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.preview_label.pixmap():
            pix = self.preview_label.pixmap()
            self.preview_label.setPixmap(pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def add_selected_to_cart(self):
        # Placeholder for cart integration
        sel = self.results_list.selectedItems()
        if not sel:
            QMessageBox.information(self, "Cart", "No items selected.")
            return
        files = [it.data(Qt.UserRole) for it in sel]
        QMessageBox.information(self, "Cart", f"Added {len(files)} file(s) to cart (stub).")

    def show_last_debug(self):
        if not self.last_debug:
            QMessageBox.information(self, "Debug", "No debug info available yet.")
            return
        dlg = DebugDialog(self.last_debug)
        dlg.exec()

    def refresh_cache(self):
        self.index.rebuild()
        QMessageBox.information(self, "Cache", "Folder index cache rebuilt.")