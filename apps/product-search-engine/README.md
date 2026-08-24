# Naturo Product Search Engine

A desktop and web search engine with catalog indexing for Naturo Surfaces.

## Directory Structure
- **`core/`**: Shared indexing engine, code/filename parsing, category taxonomy, and matching algorithms.
- **`desktop_qt/`**: Native PySide6 graphical interface with instant live search and image preview.
- **`web_app/`**: Flask REST API with PyWebView embedded web interface.

## Documentation
- **[Product & Catalog Naming Standards](../../docs/product-naming-standards.md)**: Full taxonomy, product code anatomy, PDF catalog hierarchy, and search parser specifications.

## Quick Start

### 1. Install Dependencies
```bash
make install
# or
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Desktop App (PySide6)
```bash
make run-desktop
# or
python desktop_qt/main.py
```

### 3. Run Web / PyWebView App
```bash
make run-web
# or
python web_app/app.py
```

### 4. Build Executable
```bash
make build
```
