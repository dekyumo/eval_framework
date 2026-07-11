"""Invoke AGENT5 (case_writer) to generate an EvalCase draft."""

from __future__ import annotations

import asyncio
import json

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.eval_workbench.agents.case_writer.agent import GeneratedCaseDraft
from src.eval_workbench.agents.case_writer.agent import root_agent as case_writer_agent
from src.eval_workbench.domain.snapshot import AgentSnapshot

_APP_NAME = "eval_workbench"
_USER_ID = "case_writer"
_SESSION_ID = "case_writer_gen"


def _snapshot_payload(snapshot: AgentSnapshot) -> str:
    return json.dumps(
        {
            "id": snapshot.id,
            "agent_target": snapshot.agent_target.model_dump(),
            "manifest": snapshot.manifest.model_dump() if snapshot.manifest else {},
            "distribution": snapshot.distribution.model_dump() if snapshot.distribution else None,
        },
        indent=2,
    )


def _fallback_draft(specification: str) -> GeneratedCaseDraft:
    return GeneratedCaseDraft(
        name="Generated case",
        conversation=[{"role": "user", "text": specification.strip() or "Hello"}],
        distribution_position="in",
        problem_type="happy",
    )


async def _run_case_writer_async(snapshot_json: str, specification: str) -> GeneratedCaseDraft:
    runner = InMemoryRunner(agent=case_writer_agent, app_name=_APP_NAME)
    await runner.session_service.create_session(
        app_name=_APP_NAME,
        user_id=_USER_ID,
        session_id=_SESSION_ID,
        state={"snapshot": snapshot_json, "user_specification": specification},
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=f"Generate an eval case for: {specification}")],
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
        raise RuntimeError("Case writer agent returned no response")

    return GeneratedCaseDraft.model_validate_json(final_text)


def draft_to_dict(draft: GeneratedCaseDraft) -> dict:
    return {
        "name": draft.name,
        "conversation": [
            {"role": turn.role, "kind": "text", "text": turn.text}
            for turn in draft.conversation
        ],
        "distribution_position": draft.distribution_position,
        "problem_type": draft.problem_type,
        "split": draft.split,
        "tool_fault": draft.tool_fault.model_dump() if draft.tool_fault else None,
        "metrics": [],
        "tags": [],
        "source": "generated",
    }


def generate_eval_case(snapshot: AgentSnapshot, specification: str) -> dict:
    """Generate an EvalCase draft dict from snapshot and user specification."""
    if not specification.strip():
        raise ValueError("Specification is required")

    snapshot_json = _snapshot_payload(snapshot)
    try:
        draft = asyncio.run(_run_case_writer_async(snapshot_json, specification))
    except Exception as exc:
        print(f"Case writer agent failed, using fallback: {exc}")
        draft = _fallback_draft(specification)

    if not draft.conversation:
        draft = _fallback_draft(specification)

    return draft_to_dict(draft)
