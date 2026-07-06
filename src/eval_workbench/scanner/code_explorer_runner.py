"""Invoke AGENT2 (code_explorer) through the ADK runner."""

from __future__ import annotations

import asyncio
import json
import uuid

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.eval_workbench.agents.code_explorer.agent import CodeExplorerOutput
from src.eval_workbench.agents.code_explorer.agent import root_agent as code_explorer_agent
from src.eval_workbench.ssl_config import configure_process_ssl

_APP_NAME = "eval_workbench"
_USER_ID = "scanner"


async def _run_code_explorer_async(agent_scan_result: str) -> CodeExplorerOutput:
    configure_process_ssl()
    session_id = f"code_explorer_{uuid.uuid4().hex[:8]}"
    runner = InMemoryRunner(agent=code_explorer_agent, app_name=_APP_NAME)
    await runner.session_service.create_session(
        app_name=_APP_NAME,
        user_id=_USER_ID,
        session_id=session_id,
        state={"agent_scan_result": agent_scan_result},
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text="Analyze the agent structure and draft its distribution boundaries."
            )
        ],
    )

    final_text = None
    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=session_id,
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
        raise RuntimeError("Code explorer agent returned no response")

    return CodeExplorerOutput.model_validate_json(final_text)


def run_code_explorer(agent_graph: dict) -> CodeExplorerOutput:
    """Run AGENT2 with the scan result injected into session state."""
    payload = {
        "root_agent_name": agent_graph.get("root_agent_name"),
        "agent_tree": agent_graph.get("structure", agent_graph),
        "manifest": {
            "agents": agent_graph.get("agents", []),
            "tools": agent_graph.get("tools", []),
            "prompts": agent_graph.get("prompts", []),
        },
    }
    agent_scan_result = json.dumps(payload, indent=2)
    return asyncio.run(_run_code_explorer_async(agent_scan_result))
