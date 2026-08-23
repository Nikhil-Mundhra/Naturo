import os
import sys
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog
)
from PySide6.QtCore import Qt


# -------------------------
# Build Folder + File Tree
# -------------------------

def build_folder_tree(root_path):
    """
    Recursively build a dictionary-based folder tree with files included.
    Example:
    {
        "_path": "full_path",
        "_files": ["file1.jpg", "file2.png"],
        "Subfolder": { ... }
    }
    """
    tree = {"_path": root_path, "_files": []}
    try:
        for entry in os.scandir(root_path):
            if entry.is_dir():
                tree[entry.name] = build_folder_tree(entry.path)
            elif entry.is_file():
                tree["_files"].append(entry.name)
    except PermissionError:
        pass  # skip restricted folders
    return tree


# -------------------------
# Tree Utilities
# -------------------------

def find_supplier_folder(tree, supplier_code):
    """
    Search recursively for supplier folder by code.
    """
    for name, subtree in tree.items():
        if name.startswith("_"):
            continue
        if supplier_code.lower() in name.lower():
            return subtree
        if isinstance(subtree, dict):
            result = find_supplier_folder(subtree, supplier_code)
            if result:
                return result
    return None


def find_folder_code(tree, folder_code):
    """
    Search recursively for a folder containing the folder_code in its name.
    """
    for name, subtree in tree.items():
        if name.startswith("_"):
            continue
        if folder_code.lower() in name.lower():
            return subtree
        if isinstance(subtree, dict):
            result = find_folder_code(subtree, folder_code)
            if result:
                return result
    return None


def search_files_in_tree(tree, tokens, debug_log):
    """
    Scan all files in this subtree and return matches based on tokens.
    """
    matches = []
    stack = [tree]
    while stack:
        node = stack.pop()
        for f in node.get("_files", []):
            normalized = f.lower().replace("_", "").replace(" ", "")
            ok = True
            for t in tokens:
                if t.lower().replace("_", "").replace(" ", "") not in normalized:
                    debug_log.append(f"File {f} failed on token {t}")
                    ok = False
                    break
            if ok:
                matches.append(os.path.join(node["_path"], f))
        for name, subtree in node.items():
            if isinstance(subtree, dict) and not name.startswith("_"):
                stack.append(subtree)
    return matches


# -------------------------
# Main App Window
# -------------------------

class ProductSearchApp(QWidget):
    def __init__(self, root_dir):
        super().__init__()
        self.setWindowTitle("Product Search (Tree Cached)")
        self.setGeometry(200, 200, 800, 600)

        self.folder_tree = build_folder_tree(root_dir)

        layout = QVBoxLayout()

        # Input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Product Code:"))
        self.code_input = QLineEdit()
        input_layout.addWidget(self.code_input)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.handle_search)
        input_layout.addWidget(self.search_button)
        layout.addLayout(input_layout)

        # Debug Output
        self.debug_output = QTextEdit()
        self.debug_output.setReadOnly(True)
        layout.addWidget(QLabel("Debug Log:"))
        layout.addWidget(self.debug_output)

        # Tree Export Button
        self.export_button = QPushButton("Export Tree to JSON")
        self.export_button.clicked.connect(self.export_tree)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def handle_search(self):
        code = self.code_input.text().strip()
        if not code:
            return
        debug_log = []

        # Example parsing: assume supplier is last part
        parts = code.split("_")
        supplier_code = parts[-2] if len(parts) > 2 else parts[-1]
        folder_code = None
        for p in parts:
            if p.isdigit():
                folder_code = p
                break

        debug_log.append(f"Parsed supplier: {supplier_code}")
        debug_log.append(f"Parsed folder code: {folder_code}")

        supplier_tree = find_supplier_folder(self.folder_tree, supplier_code)
        if not supplier_tree:
            debug_log.append(f"Supplier {supplier_code} not found.")
            self.debug_output.setText("\n".join(debug_log))
            return

        debug_log.append(f"Found supplier folder: {supplier_tree['_path']}")

        search_tree = supplier_tree
        if folder_code:
            folder_tree = find_folder_code(supplier_tree, folder_code)
            if folder_tree:
                search_tree = folder_tree
                debug_log.append(f"Found folder {folder_code} at {search_tree['_path']}")
            else:
                debug_log.append(f"Folder code {folder_code} not found in supplier.")

        # Remaining parts as tokens
        tokens = [p for p in parts if p not in (supplier_code, folder_code)]
        debug_log.append(f"Search tokens: {tokens}")

        matches = search_files_in_tree(search_tree, tokens, debug_log)

        if matches:
            debug_log.append("Matched files:")
            for m in matches:
                debug_log.append(f"  {m}")
        else:
            debug_log.append("No matches found.")

        self.debug_output.setText("\n".join(debug_log))

    def export_tree(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Tree", "", "JSON Files (*.json)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.folder_tree, f, indent=2)
        self.debug_output.setText(f"Tree exported to {path}")


# -------------------------
# Run App
# -------------------------

if __name__ == "__main__":
    ROOT_DIR = r"/Users/nikhil/Library/CloudStorage/GoogleDrive-silkxxxroute@gmail.com/My Drive/1.Highlighter Folders"  # change to your actual path
    app = QApplication(sys.argv)
    window = ProductSearchApp(ROOT_DIR)
    window.show()
    sys.exit(app.exec())
