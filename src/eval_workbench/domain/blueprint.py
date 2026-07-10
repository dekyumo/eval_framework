"""Agent blueprints: a JSON description of a looping ADK agent.

A blueprint is instantiated server-side into a Google ADK ``LlmAgent`` whose
tools are resolved by name from the shared tool registry (see
``eval_workbench.mcp.registry``) and run synchronously to completion.
"""

from enum import Enum

from pydantic import BaseModel, Field


class BlueprintPreset(str, Enum):
    """Named building-block agents that compose into the loops."""

    registry_explorer = "RegistryExplorer"
    registry_updater = "RegistryUpdater"
    case_maker = "CaseMaker"
    case_runner = "CaseRunner"
    case_eval_runner = "CaseEvalRunner"
    campaign_runner = "CampaignRunner"
    data_writer = "DataWriter"
    scanner = "Scanner"


class AgentBlueprint(BaseModel):
    """The JSON structure a caller sends to instantiate a looping agent."""

    agent_name: str
    model: str = "gemini-2.5-flash"
    instruction: str                     # the prompt: role, tools, do-E,F-until-G, examples
    tools: list[str] = Field(default_factory=list)   # tool names resolved from the registry


class ToolCall(BaseModel):
    name: str
    args: dict = Field(default_factory=dict)
    result: str = ""                     # summarised / truncated tool result


class BlueprintRunResult(BaseModel):
    """Outcome of running a blueprint agent to completion."""

    blueprint: AgentBlueprint
    final_output: str
    transcript: list[dict] = Field(default_factory=list)   # [{role, text}, ...]
    tool_calls: list[ToolCall] = Field(default_factory=list)
