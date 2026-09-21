"""
Sari-Sari Store POS System — Application Launcher
===================================================
Run this file to start the POS system:
    python run.py           (Local PC only)
    python run.py --lan     (Enables Xiaomi Pad / Tablet access over Starlink Wi-Fi)

The app will be available at:
    Local Cashier:  http://localhost:8000
    Admin:          http://localhost:8000/admin
"""

import uvicorn
import webbrowser
import threading
import time
import os
import sys
import socket


def get_lan_ip() -> str:
    """Retrieve the primary local IP on the Wi-Fi/Ethernet network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def open_browser():
    """Open the default browser to the cashier page after a short delay."""
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    enable_lan = "--lan" in sys.argv or os.environ.get("POS_HOST") == "0.0.0.0"
    host = "0.0.0.0" if enable_lan else os.environ.get("POS_HOST", "127.0.0.1")
    port = int(os.environ.get("POS_PORT", 8000))
    lan_ip = get_lan_ip()

    # Open browser in a background thread if on local PC
    if not os.environ.get("NO_BROWSER"):
        threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 60)
    print("  COLDCUT & SARI-SARI STORE POS SYSTEM")
    print(f"  Local Cashier:    http://localhost:{port}")
    if enable_lan:
        print(f"  Xiaomi Pad (LAN): http://{lan_ip}:{port}")
    else:
        print(f"  Tip: Run with 'python run.py --lan' to connect Xiaomi Pad")
    print(f"  Admin Portal:     http://localhost:{port}/admin")
    print("=" * 60)
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)

    # Start the FastAPI server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,       # Auto-reload on backend changes
        log_level="info",
    )
