from typing import Literal, Any
from pydantic import BaseModel
from src.eval_workbench.domain.manifest import AgentManifest

class AgentTarget(BaseModel):
    repo_path: str                           # git repo root of the agent-under-test (a sibling repo)
    agent_path: str                          # import path to the agent within the repo, e.g. "pkg.mod:root_agent"
    name: str                                # human label; also identifies a sub-agent when targeting one

class DistributionRegion(BaseModel):
    in_distribution: list[str] = []                # example tasks/intents the agent should handle
    margin: list[str] = []                   # boundary cases
    ood: list[str] = []                      # out-of-domain, should be refused/redirected

class AgentDistribution(BaseModel):
    snapshot_id: str
    description: str                         # NL: what this agent is for (drafted by SpecGenerator)
    regions: DistributionRegion
    editable: bool = True                    # detected per snapshot, then edited by a human in the UI

class AgentSnapshot(BaseModel):
    id: str                                  # = f"{commit_hash}:{agent_target.agent_path}"
    agent_target: AgentTarget                # which repo AND which agent within it
    commit_hash: str
    #branch: str # removed as only commits have permanent identities
    timestamp: float
    manifest: AgentManifest
    distribution: AgentDistribution | None = None         # detected per snapshot, human-editable
    sampling_params: dict                    # temperature, top_p... (part of the agent, not the run)
    dependency_lock: str                     # contents/hash of the lockfile at the commit
    framework_commit: str | None = None
