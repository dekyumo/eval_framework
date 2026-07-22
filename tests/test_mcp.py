import threading

import pytest
from werkzeug.serving import make_server

from src.eval_workbench.mcp.registry import build_registry
from src.eval_workbench.mcp.registry_internal import build_internal_registry, resolve_tools
from src.eval_workbench.mcp.signatures import assert_matching_signatures
from src.eval_workbench.mcp.tool_defs import TOOL_NAMES
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.web.app import create_app


@pytest.fixture
def api_server(tmp_path):
    app = create_app(repo_path=str(tmp_path), allow_db_wipe=True)
    server = make_server("127.0.0.1", 0, app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_build_internal_registry_contains_every_tool_name(tmp_path):
    registry = build_internal_registry(str(tmp_path))
    assert set(registry) == set(TOOL_NAMES)
    for name in TOOL_NAMES:
        assert callable(registry[name])
        assert registry[name].__name__ == name


def test_mcp_registry_matches_internal_signatures(api_server):
    internal = build_internal_registry("/unused")
    http_registry = build_registry(api_server)
    assert_matching_signatures(internal, http_registry)


def test_mcp_http_registry_create_and_list_tag(api_server, tmp_path):
    registry = build_registry(api_server)
    tag = registry["create_tag"](Tag(id="mcp-tag", name="MCP Tag", color="#336699"))
    assert tag.id == "mcp-tag"
    tags = registry["list_tags"]()
    assert any(item.id == "mcp-tag" for item in tags)


def test_resolve_tools_returns_callables_in_order(tmp_path):
    tools = resolve_tools(str(tmp_path), ["list_tags", "list_cases"])
    assert len(tools) == 2
    assert tools[0].__name__ == "list_tags"
    assert tools[1].__name__ == "list_cases"


def test_resolve_tools_unknown_name_raises(tmp_path):
    with pytest.raises(ServiceError) as exc:
        resolve_tools(str(tmp_path), ["list_tags", "made_up_tool"])
    assert exc.value.status_code == 400
    assert "Unknown tool" in exc.value.message


def test_mcp_tools_have_docstrings(api_server):
    registry = build_registry(api_server)
    for name in TOOL_NAMES:
        doc = registry[name].__doc__
        assert doc, f"{name} missing docstring"
        assert len(doc) < 200, f"{name} docstring too long for MCP context"
