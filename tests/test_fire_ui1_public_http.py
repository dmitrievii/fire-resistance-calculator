import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from standard_core.fire_ui1_http import run_server_in_thread
from standard_core.fire_ui1_public_http import create_public_server

ROOT = Path(__file__).resolve().parents[1]
PAGES_ORIGIN = "https://dmitrievii.github.io"


@pytest.fixture()
def public_ui_server():
    server = create_public_server(ROOT, host="127.0.0.1", port=0, allowed_origins=(PAGES_ORIGIN,))
    thread = run_server_in_thread(server)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield server, base
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def test_public_transport_health_is_not_local_only(public_ui_server):
    server, base = public_ui_server
    assert server.server_address[0] == "127.0.0.1"
    request = Request(base + "/api/health", headers={"Origin": PAGES_ORIGIN})
    with urlopen(request, timeout=5) as response:
        body = json.loads(response.read().decode("utf-8"))
        headers = dict(response.headers)
    assert body["status"] == "ok"
    assert body["local_only"] is False
    assert body["public_transport"] is True
    assert len(body["graph_sha256"]) == 64
    assert headers["Access-Control-Allow-Origin"] == PAGES_ORIGIN


def test_public_transport_preflight_allows_only_pages_origin(public_ui_server):
    _, base = public_ui_server
    allowed = Request(
        base + "/api/sessions",
        method="OPTIONS",
        headers={"Origin": PAGES_ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    with urlopen(allowed, timeout=5) as response:
        assert response.status == 204
        assert response.headers["Access-Control-Allow-Origin"] == PAGES_ORIGIN
        assert "POST" in response.headers["Access-Control-Allow-Methods"]

    denied = Request(
        base + "/api/sessions",
        method="OPTIONS",
        headers={"Origin": "https://example.invalid", "Access-Control-Request-Method": "POST"},
    )
    with pytest.raises(HTTPError) as exc:
        urlopen(denied, timeout=5)
    assert exc.value.code == 403


def test_pages_transport_shim_targets_public_backend_without_normative_logic():
    source = (ROOT / "fire_ui1_web" / "api-config.js").read_text(encoding="utf-8")
    assert "dmitrievii-fire-resistance-calculator-api.onrender.com" in source
    assert 'input.startsWith("/api/")' in source
    assert "standard_core" not in source
    assert "SP16" not in source and "SP554" not in source
