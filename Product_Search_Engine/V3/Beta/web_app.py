# web_app.py
import os
import json
import base64
import io
from PIL import Image
from flask import Flask, request, jsonify, send_file, render_template, abort
import threading
import webview

# Import your existing code
from V2.Final_Release.folder_index import FolderIndex
from V2.Final_Release.config import CONFIG_FILE, load_config

app = Flask(__name__, static_folder="static", template_folder="templates")

# --- Initialize FolderIndex from config ---
cfg = load_config()
ROOT_DIR = cfg.get("root_dir")
if not ROOT_DIR or not os.path.isdir(ROOT_DIR):
    raise SystemExit(f"root_dir not configured or missing in {CONFIG_FILE}. Edit config or run the Qt app to pick a folder.")

index = FolderIndex(ROOT_DIR)

# --- Helpers ---
def safe_relpath(path):
    """Return path relative to root_dir if under it, else None"""
    try:
        rp = os.path.realpath(path)
        root = os.path.realpath(ROOT_DIR)
        if rp.startswith(root):
            return os.path.relpath(rp, root)
    except Exception:
        pass
    return None

# --- Routes ---
@app.route("/")
def index_page():
    return render_template("index.html", root_basename=os.path.basename(ROOT_DIR))

@app.route("/api/search_code", methods=["POST"])
def api_search_code():
    payload = request.get_json() or {}
    code = payload.get("code", "").strip()
    if not code:
        return jsonify({"error": "empty code"}), 400
    try:
        # debug_search_files returns debug, matches
        dbg, matches = index.debug_search_files(code, max_show=200)
        return jsonify({"debug": dbg, "matches": matches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/search_qn", methods=["POST"])
def api_search_qn():
    payload = request.get_json() or {}
    # Expect selection object matching FolderIndex.search_by_selection input
    selection = payload.get("selection")
    if not selection:
        return jsonify({"error": "selection missing"}), 400
    try:
        dbg, exact, suggestions = index.search_by_selection(selection, max_suggestions=200)
        return jsonify({
            "debug": dbg,
            "exact": exact,
            "suggestions": suggestions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/thumbnail", methods=["GET"])
def api_thumbnail():
    # ?path=<absolute_or_rel_path>
    raw = request.args.get("path", "")
    if not raw:
        return jsonify({"error": "path missing"}), 400

    # Accept either an absolute path or a path relative to root
    if os.path.isabs(raw):
        fpath = raw
    else:
        fpath = os.path.join(ROOT_DIR, raw)

    if not os.path.isfile(fpath):
        return jsonify({"error": "file not found"}), 404

    # Only allow files under root for security
    rp = os.path.realpath(fpath)
    rootp = os.path.realpath(ROOT_DIR)
    if not rp.startswith(rootp):
        return jsonify({"error": "forbidden"}), 403

    try:
        img = Image.open(fpath)
        img.thumbnail((1200, 1200), Image.LANCZOS)
        buf = io.BytesIO()
        # Keep format PNG for consistent rendering
        img.save(buf, format="PNG")
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        return jsonify({"data": f"data:image/png;base64,{b64}"})
    except Exception as e:
        return jsonify({"error": "preview failed: " + str(e)}), 500

@app.route("/api/refresh_index", methods=["POST"])
def api_refresh_index():
    try:
        index.rebuild()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run Flask in thread then open webview ---
def start_server():
    app.run(host="127.0.0.1", port=8765, threaded=True)

def start():
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    # Give server a moment to bind
    url = "http://127.0.0.1:8765"
    window = webview.create_window("Naturo Surfaces — Search", url, width=1200, height=800)
    webview.start(gui='qt')  # qt works cross-platform if pywebview built with Qt; fallback to default otherwise

if __name__ == "__main__":
    start()
