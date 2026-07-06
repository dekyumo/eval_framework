"""Eval case writer agent (AGENT5)."""

from typing import Literal

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from src.eval_workbench.domain.fault import ToolFault

prompt = """You are a QA engineer generating evaluation test cases for AI agents.

You are given:
- An agent snapshot (target, manifest, and optional distribution boundaries): {snapshot}
- A user specification describing what eval case to create: {user_specification}

Use the distribution definition when present:
- in_distribution examples -> distribution_position "in"
- distribution_margin examples -> distribution_position "margin"
- out_of_distribution examples -> distribution_position "ood"

Choose problem_type from: happy, technical, adversarial, client.

Generate a realistic case name and one or more conversation turns (usually starting with a user message).
Only set tool_fault when the specification explicitly asks to test tool failure or fault injection.

Return structured JSON matching the output schema.
"""


class GeneratedConversationTurn(BaseModel):
    role: Literal["user", "assistant"] = "user"
    text: str = Field(description="Message text for this turn")


class GeneratedCaseDraft(BaseModel):
    name: str = Field(description="Short descriptive case name")
    conversation: list[GeneratedConversationTurn] = Field(
        description="Multi-turn conversation setup for the eval case"
    )
    distribution_position: Literal["in", "margin", "ood"] = "in"
    problem_type: Literal["happy", "technical", "adversarial", "client"] = "happy"
    split: Literal["train", "test"] = "test"
    tool_fault: ToolFault | None = None


root_agent = LlmAgent(
    name="case_writer",
    description="Generates eval cases from agent snapshot and user specification",
    instruction=prompt,
    output_schema=GeneratedCaseDraft,
    model="gemini-2.5-flash",
)
