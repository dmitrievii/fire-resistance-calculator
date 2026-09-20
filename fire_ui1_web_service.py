"""Public FIRE-UI1 web-service entry point for Render-compatible hosting."""
from __future__ import annotations

import os
from pathlib import Path

from standard_core.fire_ui1_public_http import create_public_server


ROOT = Path(__file__).resolve().parent


def _port() -> int:
    raw = os.environ.get("PORT", "10000")
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit("PORT must be an integer") from exc
    if not 1 <= value <= 65535:
        raise SystemExit("PORT must be in range 1..65535")
    return value


def _allowed_origins() -> tuple[str, ...]:
    raw = os.environ.get("FIRE_ALLOWED_ORIGINS", "https://dmitrievii.github.io")
    values = tuple(x.strip().rstrip("/") for x in raw.split(",") if x.strip())
    if not values:
        raise SystemExit("FIRE_ALLOWED_ORIGINS must contain at least one origin")
    return values


def main() -> None:
    server = create_public_server(
        ROOT,
        host="0.0.0.0",
        port=_port(),
        allowed_origins=_allowed_origins(),
    )
    print(
        "FIRE-UI1 public API listening on "
        f"http://{server.server_address[0]}:{server.server_address[1]} "
        f"for origins={sorted(server.fire_ui1_allowed_origins)}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
