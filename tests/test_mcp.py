import pytest

from src.eval_workbench.mcp.registry import TOOL_NAMES, build_registry, resolve_tools
from src.eval_workbench.services.errors import ServiceError


def test_build_registry_contains_every_tool_name(tmp_path):
    registry = build_registry(str(tmp_path))
    assert set(registry) == set(TOOL_NAMES)
    for name in TOOL_NAMES:
        assert callable(registry[name])
        assert registry[name].__name__ == name


def test_resolve_tools_returns_callables_in_order(tmp_path):
    repo_path = str(tmp_path)
    tools = resolve_tools(repo_path, ["list_tags", "list_cases"])
    assert len(tools) == 2
    assert tools[0].__name__ == "list_tags"
    assert tools[1].__name__ == "list_cases"


def test_resolve_tools_unknown_name_raises(tmp_path):
    with pytest.raises(ServiceError) as exc:
        resolve_tools(str(tmp_path), ["list_tags", "made_up_tool"])
    assert exc.value.status_code == 400
    assert "Unknown tool" in exc.value.message
