"""stdio MCP server exposing the eval workbench tool registry.

Preferred entry: ``python run_app.py <repo> --mode mcp`` (repo as positional arg).

This module is also used by ``python -m src.eval_workbench.mcp`` and the
``eval-workbench-mcp`` console script (repo from ``EVAL_WORKBENCH_REPO`` or CWD).
Both load dotenv before serving so LLM tools have API keys."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from src.eval_workbench.mcp.registry import build_registry


def build_server(repo_path: str) -> FastMCP:
    """Build the MCP server, registering every registry tool (plus run_blueprint).

    Returns the server instance to be served over stdio.
    """
    mcp = FastMCP("eval_workbench_mcp")
    registry = build_registry(repo_path)
    for name, fn in registry.items():
        mcp.add_tool(fn, name=name)
    return mcp


def main() -> None:
    """Console entry point: resolve repo path, build server, serve over stdio."""
    import dotenv

    dotenv.load_dotenv()
    repo_path = os.environ.get("EVAL_WORKBENCH_REPO", os.getcwd())
    server = build_server(repo_path)
    server.run(transport="stdio")
