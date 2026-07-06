from typing import Literal
from pydantic import BaseModel

class PromptNode(BaseModel):
    id: str
    fingerprint: str                         # of the RAW ADK instruction template, pre-.format
    text: str

class ToolNode(BaseModel):
    id: str
    name: str
    signature: str
    source_fingerprint: str
    reaches_external: bool = False           # declared external access (functional spec §11.2)

class ModelNode(BaseModel):
    id: str                                  # fully qualified, pinned (reject "latest")
    provider: str

class AgentNode(BaseModel):
    name: str
    model_id: str
    prompt_id: str
    tool_ids: list[str] = []
    skill_ids: list[str] = []
    hook_ids: list[str] = []
    subagent_names: list[str] = []

class AgentManifest(BaseModel):
    agents: list[AgentNode]
    tools: list[ToolNode]
    models: list[ModelNode]
    prompts: list[PromptNode]
    root_agent_name: str
