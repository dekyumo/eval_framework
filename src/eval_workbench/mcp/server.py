"""stdio MCP server exposing the eval workbench tool registry.

Connect to a **running** eval workbench web server via HTTP so MCP and the UI
share one Kuzu database.

Preferred entry::

    # terminal 1
    python run_app.py <repo> --mode web

    # terminal 2
    set EVAL_WORKBENCH_API_URL=http://127.0.0.1:5000
    python run_app.py <repo> --mode mcp

Also: ``python -m src.eval_workbench.mcp`` and the ``eval-workbench-mcp`` console
script (``EVAL_WORKBENCH_API_URL`` required).
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from src.eval_workbench.mcp.api_client import ApiClient
from src.eval_workbench.mcp.registry import build_registry
from src.eval_workbench.mcp.registry_internal import build_internal_registry
from src.eval_workbench.mcp.signatures import assert_matching_signatures


def resolve_api_url(explicit: str | None = None) -> str:
    api_url = explicit or os.environ.get("EVAL_WORKBENCH_API_URL", "")
    if not api_url:
        raise RuntimeError(
            "EVAL_WORKBENCH_API_URL is required for MCP mode "
            "(e.g. http://127.0.0.1:5000). Start the web server first."
        )
    return api_url


def build_server(api_url: str) -> FastMCP:
    """Build the MCP server, registering every HTTP-backed registry tool."""
    client = ApiClient(api_url)
    client.get("/api/health")

    registry = build_registry(api_url)
    reference = build_internal_registry("/unused")
    assert_matching_signatures(reference, registry)

    mcp = FastMCP("eval_workbench_mcp")
    for name, fn in registry.items():
        mcp.add_tool(fn, name=name)
    return mcp


def main() -> None:
    """Console entry point: resolve API URL, build server, serve over stdio."""
    import dotenv

    dotenv.load_dotenv()
    api_url = resolve_api_url()
    server = build_server(api_url)
    server.run(transport="stdio")
