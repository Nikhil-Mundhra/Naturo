# Makefile for Naturo Product Search Engine
PY        := python3
VENV_DIR  := .venv
PYTHON    := $(VENV_DIR)/bin/python
PIP       := $(VENV_DIR)/bin/pip

.PHONY: venv install run-desktop run-web build clean

venv:
	$(PY) -m venv $(VENV_DIR)

install: venv
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

run-desktop: venv
	$(PYTHON) desktop_qt/main.py

run-web: venv
	$(PYTHON) web_app/app.py

build: venv
	$(PYTHON) -m PyInstaller \
		--noconfirm \
		--onefile \
		--windowed \
		--name NaturoProductSearch \
		--add-data "core:core" \
		--add-data "desktop_qt:desktop_qt" \
		desktop_qt/main.py

clean:
	rm -rf $(VENV_DIR) __pycache__ dist build *.spec
	rm -rf naturo_config.json folder_tree.json
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
