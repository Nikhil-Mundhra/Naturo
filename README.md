# Naturo

Monorepo for Naturo Industries software tools, catalog search systems, and business automation utilities.

Official Website: [https://naturoindustries.com](https://naturoindustries.com)

---

## Applications & Web Services

| Project | Technology | Description |
| :--- | :--- | :--- |
| **[Product Search Engine](apps/product-search-engine/)** | Python, PySide6, Flask, PyWebView | Catalog indexing, product code parsing, and interactive search |
| **[WhatsApp Bulk Sender](apps/whatsapp-bulk-sender/)** | Python, Streamlit, Meta Graph API | Automated personalized bulk messaging |
| **[vCard & QR Generator](apps/vcard-generator/)** | Python, QR Code, HTML/CSS | Digital visiting card viewer and vCard 3.0 generator |
| **[Official Website](naturoindustries.com/)** | HTML5, CSS3, JavaScript, Vite | Naturo Industries corporate website & product showcases |

---

## Directory Overview

```
Naturo/
├── apps/                                  # Production applications & tools
│   ├── product-search-engine/             # Catalog search system (Core, Qt GUI, Web)
│   ├── whatsapp-bulk-sender/              # Bulk messaging app
│   └── vcard-generator/                   # Digital visiting card & generator
├── naturoindustries.com/                  # Official corporate website
├── docs/                                  # Setup guides & architecture documentation
│   ├── mysql-setup/                       # MySQL database setup guide & screenshots
│   └── architecture.md                    # System architecture overview
├── scripts/                               # Developer & maintenance scripts
│   └── autocommit.sh                      # Git auto-commit helper
├── archive/                               # Historical & prototype scripts
│   └── legacy-product-search/             # Archived V1, Tkinter & prototype versions
├── .gitignore                             # Ignore rules for builds, caches & temp files
└── README.md                              # Main documentation
```

---

## Development

Each application under `apps/` is fully self-contained with its own `requirements.txt` and `README.md`. Refer to individual application README files for specific instructions.
