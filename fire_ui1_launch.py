"""Launch the FIRE-UI1 guided calculator in the default local web browser."""
from __future__ import annotations

import argparse
from pathlib import Path
import webbrowser

from standard_core.fire_ui1_http import create_local_server


def main() -> None:
    """Run the loopback-only FIRE-UI1 browser application until interrupted."""
    parser = argparse.ArgumentParser(description="FIRE-UI1 local guided fire-resistance calculator")
    parser.add_argument("--port", type=int, default=8765, help="loopback port; use 0 to choose a free port")
    parser.add_argument("--no-browser", action="store_true", help="do not open the default browser")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    server = create_local_server(root, port=args.port)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    print("FIRE-UI1.5 — Engineering Guided Calculation")
    print(f"Local URL: {url}")
    print("No public network listener is used. Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
