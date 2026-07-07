"""Alsada GEO toolkit as a local HTTP service.

- ``GET /api/client`` — the configured client profile and prompt count.
- ``POST /api/analyze`` — analyze one AI answer (``{"answer": "..."}``,
  optional ``{"client": {...}}`` override) and return mention/prominence/
  sentiment/competitors/citations/flags — the same engine the measurement
  pipeline uses.

Live engine interrogation (``run``) stays CLI-only: it may call external AI
providers and spend credits, so it is not exposed over the network.
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from typing import Any

from .analyze import analyze
from .config import load_client, load_prompts
from .http_base import BaseServiceHandler, build_server


def _analyze_route(data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    answer = str(data.get("answer") or "")
    if not answer.strip():
        return 400, {"ok": False, "error": "missing 'answer'"}
    client = data.get("client") if isinstance(data.get("client"), dict) else load_client()
    return 200, {"ok": True, **analyze(answer, client)}


def _client_route() -> tuple[int, dict[str, Any]]:
    client = load_client()
    prompts = load_prompts()
    return 200, {
        "ok": True,
        "name": client.get("name"),
        "domain": client.get("domain"),
        "aliases": client.get("aliases", []),
        "competitors": client.get("competitors", []),
        "prompt_count": len(prompts),
    }


class Handler(BaseServiceHandler):
    post_routes = {"/api/analyze": staticmethod(_analyze_route)}
    get_routes = {"/api/client": staticmethod(_client_route)}


def create_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    return build_server(Handler, host=host, port=port)


def run_server(host: str | None = None, port: int | None = None) -> None:
    from .version import __version__

    server = create_server(host=host, port=port)
    print(f"alsada service v{__version__}: http://{server.server_address[0]}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
