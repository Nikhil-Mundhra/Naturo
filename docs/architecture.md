# Naturo Repository Architecture

## Overview
This repository contains internal business tools, catalog search systems, marketing assets, setup documentation, and the corporate website for Naturo Industries.

```
Naturo/
├── apps/                                  # Standalone production applications
│   ├── product-search-engine/             # Catalog search system (Core, Qt GUI, Web)
│   │   ├── core/                          # Shared business logic, indexing & parsing
│   │   ├── desktop_qt/                    # PySide6 desktop GUI
│   │   └── web_app/                       # Flask API & PyWebView web interface
│   ├── whatsapp-bulk-sender/              # Streamlit bulk messaging tool (Meta Cloud API)
│   │   └── packaging/                     # PyInstaller desktop bundling specs
│   └── vcard-generator/                   # Digital business card & QR code generator
│       ├── web/                           # Mobile-friendly HTML card viewer
│       └── assets/                        # vCard 3.0 contact cards
├── naturoindustries.com/                  # Official corporate website (Vite / Node.js)
├── docs/                                  # Setup guides & technical documentation
│   └── mysql-setup/                       # MySQL database setup guide & screenshots
├── scripts/                               # Maintenance & automation scripts
│   └── autocommit.sh                      # Git automated backup/commit helper
└── archive/                               # Preserved historical prototypes
    └── legacy-product-search/             # Archived V1 Tkinter & legacy scripts
```

## Modular Design Principles
1. **Self-Contained Applications**: Each directory under `apps/` contains its own `requirements.txt` and `README.md`, allowing isolated execution and independent virtual environments.
2. **Decoupled Business Logic**: `apps/product-search-engine/core/` provides pure data parsing and indexing logic without hard dependencies on UI frameworks, enabling multiple frontends (`desktop_qt/`, `web_app/`) to share the exact same catalog cache and search algorithms.
3. **Clean Git Hygiene**: Build outputs (`dist/`, `build/`), local caches (`folder_tree.json`), and system files are excluded from Git via `.gitignore`.
