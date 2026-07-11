import subprocess
from pathlib import Path

import pytest

from src.eval_workbench.domain.case import EvalCase
from src.eval_workbench.domain.fault import ToolFault
from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.domain.trace import MessagePart
from src.eval_workbench.faults.injector import (
    _tool_name,
    apply_tool_fault,
    ensure_mocked_tools,
)
from src.eval_workbench.repo_layout import mocked_tools_path, sanitize_agent_path
from src.eval_workbench.runner.agent_runner import AgentRunner
from src.eval_workbench.storage.kuzu_store import close_all, get_connection
from src.eval_workbench.storage.repositories import EvalCaseRepository


class _BuiltinTool:
    __module__ = "google.adk.tools.example"
    name = "google_search"

    def __call__(self, *args, **kwargs):
        return {"results": "real"}


class _PlainAgent:
    def __init__(self, tools):
        self.tools = tools
        self.sub_agents = []
        self.before_tool_callback = None


def test_sanitize_agent_path():
    assert sanitize_agent_path("a_single_agent.day_trip:root_agent") == "a_single_agent_day_trip_root_agent"


def test_mocked_tools_path_uses_sanitized_agent_path(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    path = mocked_tools_path(repo, "a_single_agent.day_trip:root_agent")
    assert path.name == "a_single_agent_day_trip_root_agent.py"
    assert path.parent.name == "mocked_tools"


def test_apply_tool_fault_creates_mock_file_and_replaces_plain_tool(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def my_tool(query: str) -> dict:
        return {"query": query, "ok": True}

    agent = _PlainAgent(tools=[my_tool])
    tool_fault = ToolFault(tool_name="my_tool", fault_type="interface")

    apply_tool_fault(agent, str(repo), "agent:root_agent", tool_fault)

    mock_path = mocked_tools_path(repo, "agent:root_agent")
    assert mock_path.exists()
    assert "MOCKS" in mock_path.read_text(encoding="utf-8")
    assert _tool_name(agent.tools[0]) == "mock_my_tool"


def test_apply_tool_fault_keeps_builtin_tool_and_sets_callback(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    builtin = _BuiltinTool()
    agent = _PlainAgent(tools=[builtin])
    tool_fault = ToolFault(tool_name="google_search", fault_type="interface")

    apply_tool_fault(agent, str(repo), "agent:root_agent", tool_fault)

    assert agent.tools[0] is builtin
    assert agent.before_tool_callback is not None
    result = agent.before_tool_callback("google_search", {"query": "paris"})
    assert isinstance(result, dict)


def test_eval_case_tool_fault_storage_roundtrip(tmp_path):
    repo_path = str(tmp_path / "agent_repo")
    Path(repo_path).mkdir()

    try:
        conn = get_connection(repo_path)
        case = EvalCase(
            id="case_fault",
            name="Fault case",
            dataset_id="ds1",
            conversation=[MessagePart(role="user", kind="text", text="hello")],
            distribution_position="in",
            problem_type="technical",
            tool_fault=ToolFault(tool_name="google_search", fault_type="interface"),
        )
        EvalCaseRepository(conn).save(case)

        loaded = EvalCaseRepository(conn).get("case_fault")
        assert loaded is not None
        assert loaded.tool_fault is not None
        assert loaded.tool_fault.tool_name == "google_search"
        assert loaded.tool_fault.fault_type == "interface"
    finally:
        close_all()


def test_agent_runner_with_tool_fault(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True)

    agent_code = """
class Agent:
    def __init__(self, name, instructions, tools):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        self.sub_agents = []
        self.before_tool_callback = None

def my_tool(x: int) -> int:
    return x * 2

root_agent = Agent(
    name="root_agent",
    instructions="You are a helpful assistant.",
    tools=[my_tool]
)
"""
    (repo / "agent.py").write_text(agent_code)
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True
    ).stdout.strip()

    target = AgentTarget(repo_path=str(repo.absolute()), agent_path="agent:root_agent", name="root")
    snapshot = AgentSnapshot(
        id=f"{commit}:agent:root_agent",
        agent_target=target,
        commit_hash=commit,
        timestamp=0.0,
        manifest=AgentManifest(agents=[], tools=[], models=[], prompts=[], root_agent_name="root"),
        sampling_params={},
        dependency_lock="",
    )

    case = EvalCase(
        id="case1",
        dataset_id="ds1",
        conversation=[MessagePart(role="user", kind="text", text="Hello")],
        distribution_position="in",
        problem_type="happy",
        tool_fault=ToolFault(tool_name="my_tool", fault_type="interface"),
    )

    trace = AgentRunner(snapshot).run_case(case, model_id="gemini-2.5-flash")

    mock_path = mocked_tools_path(repo, "agent:root_agent")
    assert mock_path.exists()
    assert "MOCKS" in mock_path.read_text(encoding="utf-8")
    assert trace.id.startswith("trace_")
