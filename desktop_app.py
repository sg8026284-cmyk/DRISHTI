import os
import sys
import threading
import uvicorn
import webview
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import existing app instance from main
from main import app

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Resolve absolute path to frontend
base_path = get_base_path()
frontend_dir = os.path.join(base_path, "frontend")

# Serve index.html directly on root "/"
@app.get("/", include_in_schema=False)
def serve_home():
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": f"Frontend directory not found at {frontend_dir}"}

# Mount static files if needed
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Open Native Window
    window = webview.create_window(
        title="DRISTI AI — Disaster Risk Intelligence & Safe Transit Interface",
        url="http://127.0.0.1:8000",
        width=1300,
        height=860,
        min_size=(1024, 700)
    )
    webview.start()