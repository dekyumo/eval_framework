import pytest
import subprocess
from pathlib import Path
from src.eval_workbench.scanner.scanner import scan_agent
from src.eval_workbench.domain.snapshot import AgentTarget

def test_scan_clean_agent(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    
    subprocess.run(["git", "init"], cwd=str(repo), check=True)
    
    agent_code = """
from pydantic import BaseModel

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
    
    target = AgentTarget(repo_path=str(repo), agent_path="agent:root_agent", name="root")
    
    manifest, distribution = scan_agent(target, commit)
    assert manifest.root_agent_name == "root_agent"
    assert len(manifest.tools) == 1
    assert manifest.tools[0].name == "my_tool"
    assert len(manifest.prompts) == 1
    assert manifest.prompts[0].text == "You are a helpful assistant."
