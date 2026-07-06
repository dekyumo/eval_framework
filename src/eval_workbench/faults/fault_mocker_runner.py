"""Invoke AGENT3 (fault_mocker) to generate mocked_tools.py."""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.eval_workbench.agents.fault_mocker.agent import MockToolReturnType
from src.eval_workbench.agents.fault_mocker.agent import root_agent as fault_mocker_agent
from src.eval_workbench.repo_layout import mocked_tools_path
from src.eval_workbench.scanner.agent_structure_dump import explore_agent

_APP_NAME = "eval_workbench"
_USER_ID = "fault_mocker"
_SESSION_ID = "fault_mocker_gen"


def _tool_sources_payload(agent: Any) -> str:
    structure = explore_agent(agent)
    tools: list[dict] = []

    def walk(node: dict) -> None:
        for tool in node.get("tools", []):
            tools.append(tool)
        for sub in node.get("sub_agents", []):
            if "_ref" not in sub:
                walk(sub)

    walk(structure)
    return json.dumps({"agent_tree": structure, "tools": tools}, indent=2)


def _fallback_mocked_tools(agent: Any) -> str:
    names: list[str] = []

    def collect(agent_node: Any) -> None:
        for tool in getattr(agent_node, "tools", None) or []:
            if hasattr(tool, "name") and isinstance(tool.name, str):
                names.append(tool.name)
            elif inspect.isfunction(tool) or callable(tool):
                names.append(getattr(tool, "__name__", "tool"))
            else:
                names.append(type(tool).__name__)
        for sub in getattr(agent_node, "sub_agents", None) or []:
            collect(sub)

    collect(agent)
    unique_names = list(dict.fromkeys(names)) or ["tool"]

    lines = ["# Generated fallback mocked_tools.py", ""]
    lines.append("MOCKS = {}")
    lines.append("")
    for name in unique_names:
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
        lines.extend([
            f"def mock_{safe}(args: dict, fault_config):",
            "    return {}",
            "",
            f"MOCKS[{name!r}] = mock_{safe}",
            "",
        ])
    return "\n".join(lines)


async def _run_fault_mocker_async(tool_sources: str) -> str:
    runner = InMemoryRunner(agent=fault_mocker_agent, app_name=_APP_NAME)
    await runner.session_service.create_session(
        app_name=_APP_NAME,
        user_id=_USER_ID,
        session_id=_SESSION_ID,
        state={"tool_sources": tool_sources},
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text="Generate mocked_tools.py for the provided agent tools.")],
    )

    final_text = None
    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=_SESSION_ID,
        new_message=message,
    ):
        if not event.is_final_response() or not event.content or not event.content.parts:
            continue
        text_parts = [
            part.text
            for part in event.content.parts
            if part.text and not getattr(part, "thought", False)
        ]
        if text_parts:
            final_text = "".join(text_parts)

    if not final_text or not final_text.strip():
        raise RuntimeError("Fault mocker agent returned no response")

    parsed = MockToolReturnType.model_validate_json(final_text)
    return parsed.mocked_tool_source_code


def generate_mocked_tools(repo_path: str | Path, agent: Any, agent_path: str) -> str:
    """Generate mocked_tools.py for an agent and return its path."""
    output_path = mocked_tools_path(repo_path, agent_path)

    try:
        source = asyncio.run(_run_fault_mocker_async(_tool_sources_payload(agent)))
    except Exception as exc:
        print(f"Fault mocker agent failed, using fallback: {exc}")
        source = _fallback_mocked_tools(agent)

    if "MOCKS" not in source:
        source = _fallback_mocked_tools(agent)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(source, encoding="utf-8")
    return str(output_path)
