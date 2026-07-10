import subprocess
from pathlib import Path

import pytest

pytest.importorskip("libcst")

from src.eval_workbench.scanner.ast_enrichment import (
    _describe_special_tool,
    enrich_scan_result,
    transitive_closure,
    ProjectIndex,
)


def _init_repo(tmp_path: Path, filename: str, content: str) -> str:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True)
    (repo / filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_describe_special_tools():
    assert "Gemini" in _describe_special_tool({"name": "google_search", "kind": "object"})  # type: ignore[arg-type]
    assert "sub-agent" in _describe_special_tool({"name": "AgentTool", "kind": "object"})  # type: ignore[arg-type]
    assert "MCP" in _describe_special_tool({"name": "McpToolset", "kind": "object"})  # type: ignore[arg-type]


def test_transitive_closure_includes_callee(tmp_path):
    commit = _init_repo(
        tmp_path,
        "agent.py",
        '''
def _helper():
    return 42

def my_tool(x: int) -> int:
    return _helper() + x
''',
    )
    repo = tmp_path / "repo"
    index = ProjectIndex(repo, commit)
    closure = transitive_closure(index, "agent", "my_tool")
    assert len(closure) == 2
    assert "my_tool" in closure[0]
    assert "_helper" in closure[1]


def test_enrich_scan_result_adds_closure_sources(tmp_path):
    commit = _init_repo(
        tmp_path,
        "agent.py",
        '''
def _helper():
    return 1

def my_tool(x: int) -> int:
    return _helper()
''',
    )
    repo = tmp_path / "repo"
    scan = {
        "tools": [{"id": "my_tool", "name": "my_tool", "module": "agent", "kind": "function"}],
        "structure": {
            "name": "root",
            "tools": [{"id": "my_tool", "name": "my_tool", "module": "agent", "kind": "function"}],
            "callbacks": [],
            "sub_agents": [],
        },
    }
    enriched = enrich_scan_result(scan, repo, commit)
    tool = enriched["tools"][0]
    assert "closure_sources" in tool
    assert len(tool["closure_sources"]) == 2
    assert "my_tool" in tool["source"]
    assert "_helper" in tool["source"]


def test_enrich_builtin_tool_description(tmp_path):
    from src.eval_workbench.scanner.ast_enrichment import ProjectIndex, enrich_callable

    commit = _init_repo(tmp_path, "agent.py", "def f(): pass\n")
    repo = tmp_path / "repo"
    item = {"id": "google_search", "name": "google_search", "kind": "object", "module": "google.adk.tools"}
    enrich_callable(item, ProjectIndex(repo, commit))
    assert item.get("source")
    assert "Gemini" in item["source"]
