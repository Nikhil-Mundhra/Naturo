import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from .config import load_config, save_config, pick_root_dir
from .folder_index import FolderIndex
from .ui_search_tab import SearchTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Naturo Surfaces App")
        self.resize(1200, 800)

        cfg = load_config()
        root_dir = cfg.get("root_dir")
        if not root_dir:
            root_dir = pick_root_dir()
            if not root_dir:
                raise SystemExit("No root directory selected.")
            cfg["root_dir"] = root_dir
            save_config(cfg)

        self.index = FolderIndex(root_dir)
        tab = SearchTab(root_dir, self.index)

        central = QWidget()
        v = QVBoxLayout(central)
        v.addWidget(tab)
        self.setCentralWidget(central)

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()