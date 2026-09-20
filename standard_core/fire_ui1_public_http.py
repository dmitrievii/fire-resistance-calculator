"""Public HTTP transport for FIRE-UI1.

This module adapts the existing local FIRE-UI1 application to a public web
service without changing any SP16/SP554 calculation code. The public transport
binds to an externally reachable host and adds an explicit CORS allowlist for
the GitHub Pages frontend.
"""
from __future__ import annotations

from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit

from .fire_ui1_http import FireUI1Application, FireUI1RequestHandler


class PublicFireUI1RequestHandler(FireUI1RequestHandler):
    """FIRE-UI1 request handler with strict origin-aware CORS headers."""

    @property
    def allowed_origins(self) -> frozenset[str]:
        return self.server.fire_ui1_allowed_origins  # type: ignore[attr-defined]

    def _request_origin(self) -> str | None:
        origin = self.headers.get("Origin")
        if not origin:
            return None
        return origin if origin in self.allowed_origins else None

    def _send_headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        origin = self._request_origin()
        if origin is not None:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        path = unquote(urlsplit(self.path).path)
        if not path.startswith("/api/"):
            self._error(HTTPStatus.NOT_FOUND, "not found")
            return
        requested_origin = self.headers.get("Origin")
        if requested_origin and requested_origin not in self.allowed_origins:
            self._error(HTTPStatus.FORBIDDEN, "origin is not allowed")
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Content-Length", "0")
        if requested_origin:
            self.send_header("Access-Control-Allow-Origin", requested_origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:
        path = unquote(urlsplit(self.path).path)
        if path == "/api/health":
            self._json(
                HTTPStatus.OK,
                {
                    "schema": "fire_ui1_http_api_v1",
                    "status": "ok",
                    "graph_id": self.app.model.graph["graph_id"],
                    "graph_sha256": self.app.model.graph_sha256,
                    "local_only": False,
                    "public_transport": True,
                },
            )
            return
        super().do_GET()


class PublicFireUI1HTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        app: FireUI1Application,
        allowed_origins: Iterable[str],
    ):
        super().__init__(server_address, PublicFireUI1RequestHandler)
        self.fire_ui1_app = app
        self.fire_ui1_allowed_origins = frozenset(allowed_origins)


def create_public_server(
    root: str | Path,
    *,
    host: str = "0.0.0.0",
    port: int = 10000,
    allowed_origins: Iterable[str] = ("https://dmitrievii.github.io",),
) -> PublicFireUI1HTTPServer:
    """Create the public transport while preserving the frozen calculation app."""
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be an integer from 0 to 65535")
    origins = tuple(dict.fromkeys(str(x).strip().rstrip("/") for x in allowed_origins if str(x).strip()))
    if not origins:
        raise ValueError("at least one allowed origin is required")
    if any(not origin.startswith("https://") for origin in origins):
        raise ValueError("public allowed origins must use https://")
    app = FireUI1Application.from_package_root(root)
    return PublicFireUI1HTTPServer((host, port), app, origins)
