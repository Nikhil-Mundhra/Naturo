import json, os

CONFIG_FILE = "naturo_config.json"

DEFAULT_CONFIG = {
    "theme": "light",
    "last_folder": None,
    "search_history": []
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

def update_config(key, value):
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    return cfg
