"""FIRE-UI1 local HTTP adapter for the DAG-driven guided calculator.

The adapter is intentionally thin. It exposes FIRE-UI0 application services to
an offline browser frontend over loopback HTTP and never reimplements any
SP16/SP554 equation in the transport or presentation layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from typing import Any, Mapping
from urllib.parse import parse_qs, unquote, urlsplit

from .fire_ui0 import (
    FireDAGModel,
    FireUIError,
    GuidedCalculationService,
    GuidedCalculationSession,
    ExecutionRegistry,
)
from .profile_catalog import InterimProfileCatalog
from .fire_ui13_material_strength import (
    infer_material_context, material_strength_catalog, resolve_material_preview,
)
from .fire_bridge2_qualified_state import _build_fire_bridge2_registry
from .material_resistance import SteelMaterialStrengthResolver

MAX_JSON_BYTES = 5 * 1024 * 1024
API_SCHEMA = "fire_ui1_http_api_v1"


@dataclass
class FireUI1Application:
    """
    Summary:
        Own the frozen DAG model, guided service and immutable static frontend root.

    Standard reference:
        UI/application transport only; normative meaning and calculations are inherited from the frozen SP16 ↔ SP554 DAG and FIRE-UI0 executor registry.

    Fields:
        root, model, service and web_root.

    Validation:
        Package-root construction verifies the frozen DAG and materialized frontend entry file before serving.

    Used by:
        FireUI1RequestHandler, create_local_server and the FIRE-UI1 local launcher.
    """

    root: Path
    model: FireDAGModel
    service: GuidedCalculationService
    web_root: Path
    profile_catalog: InterimProfileCatalog
    material_resolver: SteelMaterialStrengthResolver

    @classmethod
    def from_package_root(
        cls,
        root: str | Path,
        *,
        registry: ExecutionRegistry | None = None,
    ) -> "FireUI1Application":
        """Create a local UI application from one extracted cumulative package."""
        package_root = Path(root).resolve()
        dag_path = package_root / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
        presentation_path = package_root / "data" / "fire_bridge2_presentation_policy.json"
        web_root = package_root / "fire_ui1_web"
        if not dag_path.is_file():
            raise FireUIError(f"FIRE-UI1 DAG not found: {dag_path}")
        if not (web_root / "index.html").is_file():
            raise FireUIError(f"FIRE-UI1 frontend not found: {web_root}")
        if not presentation_path.is_file():
            raise FireUIError(f"FIRE-BRIDGE2 presentation policy not found: {presentation_path}")
        model = FireDAGModel.load(dag_path, presentation_policy_path=presentation_path)
        catalog = InterimProfileCatalog()
        material_resolver = SteelMaterialStrengthResolver()
        effective_registry = _build_fire_bridge2_registry(catalog, registry)
        return cls(package_root, model, GuidedCalculationService(model, registry=effective_registry), web_root, catalog, material_resolver)

    def profile_catalog_families(self) -> dict[str, Any]:
        """Return profile-family choices for the section editor."""
        return {
            "status": "INTERIM_PENDING_ORIGINAL_GOST_AUDIT",
            "family_count": self.profile_catalog.family_count,
            "profile_count": self.profile_catalog.profile_count,
            "families": self.profile_catalog.list_families(),
        }

    def profile_catalog_profiles(self, family_id: int) -> dict[str, Any]:
        """Return selectable profiles for one exact catalog family."""
        return {
            "family": self.profile_catalog.family(family_id),
            "profiles": self.profile_catalog.list_profiles(family_id),
        }

    def profile_catalog_resolve(self, family_id: int, designation: str, source_row_id: int | None) -> dict[str, Any]:
        """Resolve one exact profile row for read-only preview and deterministic payload identity."""
        return self.profile_catalog.resolve(family_id, designation, source_row_id=source_row_id)

    def material_strength_catalog(self) -> dict[str, Any]:
        """Return exact current-SP16 material rows for the compact material editor."""
        return material_strength_catalog(self.material_resolver)

    def material_strength_preview(self, product_form: str, steel_grade: str, interval_key: str) -> dict[str, Any]:
        """Resolve one exact Annex В row for read-only preview."""
        return resolve_material_preview(product_form, steel_grade, interval_key, self.material_resolver)

    def material_strength_context(self, session_id: str) -> dict[str, Any]:
        """Return non-binding material suggestions inferred from the already selected section geometry."""
        session = self.service.get_session(session_id)
        return infer_material_context(session.plain_values(), self.material_resolver)

    def ui_contract(self) -> dict[str, Any]:
        """Return the deterministic UI contract generated from the frozen DAG."""
        return self.model.build_ui_contract()

    def create_session(self) -> dict[str, Any]:
        """Create a new in-memory guided-calculation session."""
        return self.service.create_session()

    def session_payload(self, session_id: str) -> dict[str, Any]:
        """Return complete state and current card for one existing session."""
        session = self.service.get_session(session_id)
        return {
            "session_id": session_id,
            "state": session.snapshot(),
            "current_card": session.current_card(),
        }

    def restore_session(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        """Restore a saved DAG-locked snapshot into a new local session ID."""
        created = self.service.create_session()
        sid = created["session_id"]
        session = self.service.get_session(sid)
        try:
            session.restore(snapshot)
        except FireUIError:
            del self.service.sessions[sid]
            raise
        return self.session_payload(sid)

    def delete_session(self, session_id: str) -> None:
        """Delete one local in-memory session without modifying saved snapshots."""
        if session_id not in self.service.sessions:
            raise FireUIError("unknown session_id")
        del self.service.sessions[session_id]


class FireUI1RequestHandler(BaseHTTPRequestHandler):
    """
    Summary:
        Serve the offline FIRE-UI1 frontend and JSON API from one loopback HTTP origin.

    Standard reference:
        UI/application transport only; no SP16/SP554 equation is evaluated in the request handler.

    Fields:
        Uses the FireUI1Application attached to the owning HTTP server and standard BaseHTTPRequestHandler request state.

    Validation:
        JSON bodies are size-bounded and typed as objects; static paths are allowlisted; service-level validation remains fail-closed.

    Used by:
        FireUI1HTTPServer.
    """

    server_version = "FIRE-UI1/1"

    @property
    def app(self) -> FireUI1Application:
        """Return the application attached to the owning HTTP server."""
        return self.server.fire_ui1_app  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        """Keep default console logging concise and deterministic enough for local QA."""
        super().log_message(format, *args)

    def _send_headers(self, status: int, content_type: str, length: int) -> None:
        """Send common local-app response headers."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()

    def _json(self, status: int, payload: Any) -> None:
        """Serialize one UTF-8 JSON response."""
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_headers(status, "application/json; charset=utf-8", len(raw))
        self.wfile.write(raw)

    def _error(self, status: int, message: str) -> None:
        """Return a stable API error envelope without exposing Python tracebacks."""
        self._json(status, {"schema": API_SCHEMA, "error": message})

    def _read_json(self) -> dict[str, Any]:
        """Read one bounded JSON-object request body."""
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            raise FireUIError("Content-Length is required")
        try:
            length = int(raw_len)
        except ValueError as exc:
            raise FireUIError("invalid Content-Length") from exc
        if length < 0 or length > MAX_JSON_BYTES:
            raise FireUIError("JSON payload is too large")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FireUIError("request body must be valid UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise FireUIError("request JSON must be an object")
        return value

    def _static_file(self, request_path: str) -> Path | None:
        """Resolve an allowlisted static frontend path without path traversal."""
        clean = request_path.lstrip("/")
        if clean == "":
            clean = "index.html"
        allow = {
            "index.html": self.app.web_root / "index.html",
            "assets/app.js": self.app.web_root / "dist" / "app.js",
            "assets/styles.css": self.app.web_root / "styles.css",
        }
        return allow.get(clean)

    def do_GET(self) -> None:
        """Handle frontend, health, contract and session-state GET requests."""
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)
        try:
            if path == "/api/health":
                self._json(
                    HTTPStatus.OK,
                    {
                        "schema": API_SCHEMA,
                        "status": "ok",
                        "graph_id": self.app.model.graph["graph_id"],
                        "graph_sha256": self.app.model.graph_sha256,
                        "local_only": True,
                    },
                )
                return
            if path == "/api/ui-contract":
                self._json(HTTPStatus.OK, self.app.ui_contract())
                return
            if path == "/api/profile-catalog/families":
                self._json(HTTPStatus.OK, self.app.profile_catalog_families())
                return
            if path.startswith("/api/profile-catalog/families/") and path.endswith("/profiles"):
                parts = [p for p in path.split("/") if p]
                if len(parts) != 5:
                    self._error(HTTPStatus.NOT_FOUND, "unknown profile-catalog endpoint")
                    return
                try:
                    family_id = int(parts[3])
                except ValueError as exc:
                    raise FireUIError("family_id must be integer") from exc
                self._json(HTTPStatus.OK, self.app.profile_catalog_profiles(family_id))
                return
            if path == "/api/profile-catalog/resolve":
                try:
                    family_id = int(query["family_id"][0])
                    designation = query["designation"][0]
                    source_row_id = int(query["source_row_id"][0]) if "source_row_id" in query else None
                except (KeyError, ValueError, IndexError) as exc:
                    raise FireUIError("family_id and designation are required; source_row_id is optional") from exc
                self._json(HTTPStatus.OK, self.app.profile_catalog_resolve(family_id, designation, source_row_id))
                return
            if path == "/api/material-strength/catalog":
                self._json(HTTPStatus.OK, self.app.material_strength_catalog())
                return
            if path == "/api/material-strength/resolve":
                try:
                    product_form = query["product_form"][0]
                    steel_grade = query["steel_grade"][0]
                    interval_key = query["interval_key"][0]
                except (KeyError, IndexError) as exc:
                    raise FireUIError("product_form, steel_grade and interval_key are required") from exc
                self._json(HTTPStatus.OK, self.app.material_strength_preview(product_form, steel_grade, interval_key))
                return
            if path.startswith("/api/sessions/") and path.endswith("/material-strength-context"):
                parts = [p for p in path.split("/") if p]
                if len(parts) != 4:
                    self._error(HTTPStatus.NOT_FOUND, "unknown material-strength context endpoint")
                    return
                self._json(HTTPStatus.OK, self.app.material_strength_context(parts[2]))
                return
            if path.startswith("/api/sessions/"):
                parts = [p for p in path.split("/") if p]
                if len(parts) == 3:
                    self._json(HTTPStatus.OK, self.app.session_payload(parts[2]))
                    return
                if len(parts) == 4 and parts[3] in {"ledger", "trace"}:
                    session = self.app.service.get_session(parts[2])
                    payload = session.ledger() if parts[3] == "ledger" else [row.as_dict() for row in session.trace]
                    self._json(HTTPStatus.OK, payload)
                    return
                self._error(HTTPStatus.NOT_FOUND, "unknown session endpoint")
                return
            if path.startswith("/api/"):
                self._error(HTTPStatus.NOT_FOUND, "unknown API endpoint")
                return
            static_path = self._static_file(path)
            if static_path is None or not static_path.is_file():
                self._error(HTTPStatus.NOT_FOUND, "not found")
                return
            suffix = static_path.suffix.lower()
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
            }[suffix]
            data = static_path.read_bytes()
            self._send_headers(HTTPStatus.OK, content_type, len(data))
            self.wfile.write(data)
        except FireUIError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))

    def do_POST(self) -> None:
        """Handle session creation, restoration and answer submission."""
        path = unquote(urlsplit(self.path).path)
        try:
            if path == "/api/sessions":
                self._read_json()
                self._json(HTTPStatus.CREATED, self.app.create_session())
                return
            if path == "/api/sessions/restore":
                body = self._read_json()
                snapshot = body["snapshot"] if "snapshot" in body else body
                self._json(HTTPStatus.CREATED, self.app.restore_session(snapshot))
                return
            parts = [p for p in path.split("/") if p]
            if len(parts) == 4 and parts[:2] == ["api", "sessions"] and parts[3] == "answer":
                body = self._read_json()
                if "payload" not in body:
                    raise FireUIError("payload is required")
                result = self.app.service.submit(parts[2], body["payload"], provenance=body.get("provenance"))
                self._json(HTTPStatus.OK, result)
                return
            self._error(HTTPStatus.NOT_FOUND, "unknown API endpoint")
        except FireUIError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))

    def do_PUT(self) -> None:
        """Handle deterministic answer editing with downstream invalidation/replay."""
        path = unquote(urlsplit(self.path).path)
        try:
            parts = [p for p in path.split("/") if p]
            if len(parts) == 5 and parts[:2] == ["api", "sessions"] and parts[3] == "answers":
                body = self._read_json()
                if "payload" not in body:
                    raise FireUIError("payload is required")
                result = self.app.service.edit(parts[2], parts[4], body["payload"], provenance=body.get("provenance"))
                self._json(HTTPStatus.OK, result)
                return
            self._error(HTTPStatus.NOT_FOUND, "unknown API endpoint")
        except FireUIError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))

    def do_DELETE(self) -> None:
        """Delete one local session."""
        path = unquote(urlsplit(self.path).path)
        try:
            parts = [p for p in path.split("/") if p]
            if len(parts) == 3 and parts[:2] == ["api", "sessions"]:
                self.app.delete_session(parts[2])
                self._json(HTTPStatus.OK, {"schema": API_SCHEMA, "deleted": parts[2]})
                return
            self._error(HTTPStatus.NOT_FOUND, "unknown API endpoint")
        except FireUIError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))


class FireUI1HTTPServer(ThreadingHTTPServer):
    """
    Summary:
        Threading loopback HTTP server carrying a typed FIRE-UI1 application reference.

    Standard reference:
        UI/application transport only; calculation authority remains in registered production executors.

    Fields:
        fire_ui1_app plus inherited HTTP server address/socket state.

    Validation:
        Created only through the local server factory, which binds explicitly to 127.0.0.1.

    Used by:
        create_local_server, run_server_in_thread and fire_ui1_launch.py.
    """

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], app: FireUI1Application):
        super().__init__(server_address, FireUI1RequestHandler)
        self.fire_ui1_app = app


def create_local_server(
    root: str | Path,
    *,
    port: int = 8765,
    registry: ExecutionRegistry | None = None,
) -> FireUI1HTTPServer:
    """
    Summary:
        Create a loopback-only FIRE-UI1 HTTP server for one extracted cumulative package.

    Standard reference:
        UI/application transport only; the frozen normative DAG and registered production executors remain authoritative.

    Parameters:
        root: Extracted cumulative package root containing the frozen DAG and FIRE-UI1 web assets.
        port: Loopback TCP port; zero requests an operating-system-selected free port.
        registry: Optional explicit FIRE-UI0 production executor registry.

    Returns:
        Configured FireUI1HTTPServer bound to 127.0.0.1 and not yet serving requests.

    Assumptions:
        The package is internally consistent and contains the v0.3.45 SP16 D.3 interpolation-hotfix DAG expected by FIRE-UI1.

    Sign convention:
        Not applicable; transport layer does not evaluate engineering quantities.

    Unit convention:
        Units are passed through unchanged from the DAG/session ledger.

    Applicability:
        Local sequential acceptance testing and offline engineering QA for FIRE-UI1.

    Limitations:
        Does not expose a public network listener and does not bind missing normative executors.

    Raises:
        FireUIError for invalid port values, missing DAG/frontend files, or incompatible package structure.

    Examples:
        ``server = create_local_server(root, port=0)``.

    Tests:
        tests/test_fire_ui1_frontend.py covers loopback binding, health, static assets and session API behavior.

    Implementation notes:
        The host is intentionally hard-coded to 127.0.0.1; the frontend and API share one origin.
    """
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise FireUIError("port must be an integer from 0 to 65535")
    app = FireUI1Application.from_package_root(root, registry=registry)
    return FireUI1HTTPServer(("127.0.0.1", port), app)


def run_server_in_thread(server: FireUI1HTTPServer) -> threading.Thread:
    """
    Summary:
        Start an already-created FIRE-UI1 local HTTP server in a daemon thread.

    Standard reference:
        UI/application test/embedding utility only; it performs no normative calculations.

    Parameters:
        server: Configured FireUI1HTTPServer created by create_local_server.

    Returns:
        Started daemon threading.Thread running ``serve_forever``.

    Assumptions:
        The caller owns server shutdown and close lifecycle.

    Sign convention:
        Not applicable.

    Unit convention:
        Not applicable.

    Applicability:
        Automated API tests and optional embedding of the local frontend.

    Limitations:
        Not intended as a public production deployment mechanism.

    Raises:
        Standard threading/server exceptions if the supplied server cannot start.

    Examples:
        ``thread = run_server_in_thread(server)`` followed by explicit shutdown.

    Tests:
        tests/test_fire_ui1_frontend.py uses this helper for every HTTP acceptance case.

    Implementation notes:
        The thread is daemonized so failed tests do not keep the Python process alive.
    """
    thread = threading.Thread(target=server.serve_forever, name="fire-ui1-http", daemon=True)
    thread.start()
    return thread
