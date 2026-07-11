import pytest
import subprocess
import json
from pathlib import Path
from src.eval_workbench.runner.worktree import WorktreeRunner
from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.domain.case import EvalCase, MetricDef
from src.eval_workbench.domain.trace import Trace, MessagePart
from src.eval_workbench.runner.agent_runner import AgentRunner

def test_agent_runner(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True)
    
    agent_code = """
class Agent:
    def __init__(self, name, instructions, tools):
        self.name = name
        self.instructions = instructions
        self.tools = tools

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
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
    
    target = AgentTarget(repo_path=str(repo.absolute()), agent_path="agent:root_agent", name="root")
    
    snapshot = AgentSnapshot(
        id=f"{commit}:agent:root_agent",
        agent_target=target,
        commit_hash=commit,
        timestamp=0.0,
        manifest=AgentManifest(agents=[], tools=[], models=[], prompts=[], root_agent_name="root"),
        sampling_params={},
        dependency_lock=""
    )
    
    case = EvalCase(
        id="case1",
        dataset_id="ds1",
        conversation=[MessagePart(role="user", kind="text", text="Hello")],
        distribution_position="in",
        problem_type="happy"
    )
    
    runner = AgentRunner(snapshot)
    trace = runner.run_case(case, model_id="gemini-2.5-flash")
    
    assert trace.id.startswith("trace_")
    assert len(trace.parts) >= 1
    assert trace.parts[0].role == "user"
    assert trace.latency_ms >= 0
