# Makefile

# Config
PY        := python3
VENV_DIR  := .venv
PYTHON    := $(VENV_DIR)/bin/python
PIP       := $(VENV_DIR)/bin/pip

.PHONY: venv install run clean freeze upgrade deps

# Create virtual environment
venv:
	$(PY) -m venv $(VENV_DIR)

# Install project dependencies
install: venv
	$(PIP) install --upgrade pip
	# Prefer requirements.txt if you have one; otherwise install directly:
	# $(PIP) install -r requirements.txt
	$(PIP) install PySide6 pillow

# Run the app as a package (requires V2/__init__.py and V2/main.py)
run: venv
	$(PYTHON) -m V2.main

# Optional: show exact versions locked from current venv
freeze:
	$(PIP) freeze > requirements.txt

# Optional: upgrade core packaging tools
upgrade: venv
	$(PIP) install --upgrade pip setuptools wheel

# Optional: install from requirements.txt if present
deps: venv
	$(PIP) install -r requirements.txt

# Clean artifacts
clean:
	rm -rf $(VENV_DIR) __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +


# cd "/Users/nikhil/Library/CloudStorage/GoogleDrive-silkxxxroute@gmail.com/My Drive/App/"
# make clean
# make install
# make run

# test: 63_PK_PV_BL_MRP_950_
# test: 24_PK_PV_BR_MRP_975_FT_Pr_Eq_14L_12"9.5F_02_KYGH_Q8