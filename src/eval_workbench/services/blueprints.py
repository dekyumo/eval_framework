"""Blueprint service: instantiate and run a looping ADK agent to completion."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types

from src.eval_workbench.domain.blueprint import (
    AgentBlueprint,
    BlueprintPreset,
    BlueprintPresetInfo,
    BlueprintRunResult,
    ToolCall,
)
from src.eval_workbench.mcp.tool_defs import PRESET_INSTRUCTIONS, PRESET_TOOLS
from src.eval_workbench.mcp.registry_internal import resolve_tools
from src.eval_workbench.runner.trace_events import append_trace_parts_from_event
from src.eval_workbench.run_coro_sync import run_coro_sync as _run_coro_sync
from src.eval_workbench.services.errors import ServiceError

_APP_NAME = "eval_workbench"
_USER_ID = "blueprint_runner"


def list_presets() -> list[BlueprintPresetInfo]:
    """Return the available blueprint presets."""
    return [
        BlueprintPresetInfo(
            preset=preset.value,
            instruction=PRESET_INSTRUCTIONS[preset],
            tools=PRESET_TOOLS[preset],
        )
        for preset in BlueprintPreset
    ]


def _resolve_preset(preset: str) -> BlueprintPreset:
    for item in BlueprintPreset:
        if item.value == preset:
            return item
    raise ServiceError(f"Unknown preset: {preset}", 400)


def preset_blueprint(preset: str) -> AgentBlueprint:
    """Return a ready-to-run AgentBlueprint for a named preset."""
    key = _resolve_preset(preset)
    return AgentBlueprint(
        agent_name=key.value,
        instruction=PRESET_INSTRUCTIONS[key],
        tools=PRESET_TOOLS[key],
    )


def _summarize_result(value: Any, limit: int = 500) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, default=str)
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def _trace_parts_to_transcript(trace_parts: list[dict[str, Any]]) -> list[dict[str, str]]:
    transcript: list[dict[str, str]] = []
    for part in trace_parts:
        role = part.get("role", "assistant")
        if part.get("kind") == "text":
            transcript.append({"role": role, "text": part.get("text", "")})
        elif part.get("kind") == "tool_call":
            name = part.get("tool_name", "tool")
            args = json.dumps(part.get("tool_args") or {})
            transcript.append({"role": role, "text": f"Called {name}({args})"})
        elif part.get("kind") == "tool_response":
            name = part.get("tool_name", "tool")
            response = _summarize_result(part.get("tool_response"))
            transcript.append({"role": "tool", "text": f"{name}: {response}"})
    return transcript


def _tool_calls_from_trace(trace_parts: list[dict[str, Any]]) -> list[ToolCall]:
    calls: list[ToolCall] = []
    for part in trace_parts:
        if part.get("kind") != "tool_call":
            continue
        calls.append(
            ToolCall(
                name=part.get("tool_name", ""),
                args=part.get("tool_args") or {},
            )
        )
    for part in trace_parts:
        if part.get("kind") != "tool_response":
            continue
        name = part.get("tool_name", "")
        result = _summarize_result(part.get("tool_response"))
        for call in calls:
            if call.name == name and not call.result:
                call.result = result
                break
    return calls


async def _run_blueprint_async(
    blueprint: AgentBlueprint,
    tool_fns: list[Callable[..., Any]],
) -> BlueprintRunResult:
    function_tools = [
        FunctionTool(fn, name=tool_name)
        for tool_name, fn in zip(blueprint.tools, tool_fns, strict=True)
    ]
    agent = LlmAgent(
        name=blueprint.agent_name,
        model=blueprint.model,
        instruction=blueprint.instruction,
        tools=function_tools,
    )

    session_id = f"blueprint_{blueprint.agent_name}_{uuid.uuid4().hex[:8]}"
    runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
    await runner.session_service.create_session(
        app_name=_APP_NAME,
        user_id=_USER_ID,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text="Begin executing your instructions.")],
    )

    trace_parts: list[dict[str, Any]] = []

    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        append_trace_parts_from_event(event, trace_parts)

    final_output = ""
    for part in reversed(trace_parts):
        if part.get("kind") == "text" and part.get("text"):
            final_output = part["text"]
            break

    return BlueprintRunResult(
        blueprint=blueprint,
        final_output=final_output,
        transcript=_trace_parts_to_transcript(trace_parts),
        tool_calls=_tool_calls_from_trace(trace_parts),
    )


def run_blueprint(repo_path: str, blueprint: AgentBlueprint) -> BlueprintRunResult:
    """Build an ADK LlmAgent from the blueprint, resolve its tools, run to completion."""
    tool_fns = resolve_tools(repo_path, blueprint.tools)
    return _run_coro_sync(_run_blueprint_async(blueprint, tool_fns))
