# ---------------- CONFIG / CONSTANTS ----------------
CONFIG_FILE = "naturo_config.json"
TREE_CACHE_FILE = "folder_tree.json"

FILE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.pdf', '.heic', '.jfif')
IMG_EXTS  = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.pdf', '.heic', '.jfif')

COLOR_MAP = {
    "Red": "RD", "Black": "BL", "Gold": "GD", "Silver": "SV", "Teak": "TK",
    "Walnut": "WL", "Yellow": "YL", "Blue": "BU", "Steel": "ST", "Grey": "GY",
    "Brown": "BR", "White": "WT", "Purple": "PL", "Green": "GN", "Rose Gold": "RG",
    "Beage": "BG", "Cream": "CR", "Mobe": "MO", "Metalic": "MT", "Marble": "MB"
}

MATERIAL_MAP = {
    "Charcoal": "CH",
    "PVC": "PV",
    "WPC": "WP",
    "Super Heavy": "SPHV",
    "Ultra Voilet Foarm Sheet": "UVFS",
    "Ultra Voilet Marble Sheet": "UVMB",
    "Tiger Fabric": "TG",
    "Acrylic": "ACY"
}

DESIGN_CATEGORIES = {
    "Pattern Type": {
        "Flutted": "FT",
        "Equal Distance Between The Lines": "EQ",
        "Line": "L",
        "Step": "S",
        "Double Tone": "DT",
        "Rounded": "RD",
        "Louver Style": "LV"
    },
    "Surface Finish": {
        "Texture": "TX",
        "Matt": "MTT",
        "Seamless": "SL",
        "Printed": "PR",
        "Wooden": "WD"
    },
    "Special Types": {
        "Digital Marble Sheet": "DMS",
        "Flutted Marble Sheet": "FMS",
        "Book Match Digital Marble": "BMDM",
        "Digital Marble Gold Line": "DMGL",
        "High/3D Sheet": "H3D",
        "Panel No Line": "PL",
        "Volume": "VO",
        "Catalogue": "CT"
    }
}

# Derived design maps
DESIGN_MAP = {}
for cat in DESIGN_CATEGORIES.values():
    DESIGN_MAP.update(cat)
DESIGN_CODES_LOWER = {v.lower() for v in DESIGN_MAP.values()}

SUPPLIER_CODES = {
    "RYPP", "MHPP", "JAWD", "GSPD", "MPKD", "NXSP", "LPSM", "DSSP", "JGSP",
    "ETNU", "HEHH", "SWSP", "KYKN", "KKGH", "OJLD", "RKGD", "LVGU", "MUNU",
    "SSSG", "LDZP", "STSG", "DERG", "SSSD", "KYGH", "REPP", "HCIM"
}
SUPPLIER_CODES_LOWER = {s.lower() for s in SUPPLIER_CODES}

# UI sizing
HEIGHT_COLLAPSED_QN = 65
HEIGHT_SEARCH = 120
HEIGHT_QN = 900
