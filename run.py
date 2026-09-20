"""
Sari-Sari Store POS System — Application Launcher
===================================================
Run this file to start the POS system:
    python run.py

The app will be available at:
    Cashier:  http://localhost:8000
    Admin:    http://localhost:8000/admin
"""

import uvicorn
import webbrowser
import threading
import time
import os


def open_browser():
    """Open the default browser to the cashier page after a short delay."""
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    # Open browser in a background thread so it doesn't block the server
    threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 50)
    print("  SARI-SARI STORE POS SYSTEM")
    print("  Cashier:  http://localhost:8000")
    print("  Admin:    http://localhost:8000/admin")
    print("=" * 50)
    print("  Press Ctrl+C to stop the server")
    print("=" * 50)

    host = os.environ.get("POS_HOST", "127.0.0.1")
    port = int(os.environ.get("POS_PORT", 8000))

    # Start the FastAPI server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,       # Auto-reload on backend changes
        log_level="info",
    )
