# Makefile for Naturo Product Search V2
# ----------------------
# Usage:
#   make clean      # remove build artifacts
#   make install    # setup venv and dependencies
#   make run        # run app from venv
#   make build      # build executable
# ----------------------

# Config
PY        := python3
VENV_DIR  := .venv
PYTHON    := $(VENV_DIR)/bin/python
PIP       := $(VENV_DIR)/bin/pip

# Detect OS for PyInstaller --add-data syntax
ifeq ($(OS),Windows_NT)
    ADDDATA := Final_Release;Final_Release
    EXE_EXT := .exe
else
    ADDDATA := Final_Release:Final_Release
    EXE_EXT :=
endif

.PHONY: venv install run build clean freeze upgrade deps


# ----------------------
# Virtual environment
# ----------------------
venv:
	$(PY) -m venv $(VENV_DIR)

# ----------------------
# Install dependencies
# ----------------------
install: venv
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt || true
	$(PIP) install PySide6 pillow flask pywebview pyinstaller

# ----------------------
# Run the app
# ----------------------
run: venv
	$(PYTHON) -m Final_Release.main


# ----------------------
# Build executable
# ----------------------
build: venv
	$(PYTHON) -m PyInstaller \
		--noconfirm \
		--onefile \
		--windowed \
		--name NaturoApp$(EXE_EXT) \
		--add-data "$(ADDDATA)" \
		Final_Release/main.py


# ----------------------
# Freeze dependencies
# ----------------------
freeze:
	$(PIP) freeze > requirements.txt


# ----------------------
# Upgrade pip/setuptools/wheel
# ----------------------
upgrade: venv
	$(PIP) install --upgrade pip setuptools wheel

# ----------------------
# Install from requirements.txt
# ----------------------
deps: venv
	$(PIP) install -r requirements.txt

# ----------------------
# Clean artifacts
# ----------------------
clean:
	rm -rf $(VENV_DIR) __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf naturo_config.json folder_tree.json
	rm -rf dist build NaturoApp.spec
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +


# cd "/Users/nikhil/Library/CloudStorage/GoogleDrive-silkxxxroute@gmail.com/My Drive/App/"
# make clean
# make install
# make run

# test: 63_PK_PV_BL_MRP_950_
# test: 24_PK_PV_BR_MRP_975_FT_Pr_Eq_14L_12"9.5F_02_KYGH_Q8