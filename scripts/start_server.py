"""BookVoice OCR Studio launcher.
Finds an available port, opens the browser, and starts uvicorn.
"""
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def find_port():
    """Find a free port starting from 8888."""
    for port in range(8888, 9100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            continue
    raise RuntimeError("No available port found")


def open_browser(port):
    time.sleep(2)
    webbrowser.open(f"http://127.0.0.1:{port}")


def main():
    port = find_port()
    print(f"\n  BookVoice OCR Studio")
    print(f"  ====================")
    print(f"  URL: http://127.0.0.1:{port}")
    print(f"  Close this window to stop.\n")

    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)


if __name__ == "__main__":
    main()
