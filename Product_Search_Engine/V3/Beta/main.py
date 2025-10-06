import webview
from backend.api import Api

if __name__ == "__main__":
    api = Api()
    window = webview.create_window("Naturo Search", "frontend/index.html", js_api=api)
    webview.start()
