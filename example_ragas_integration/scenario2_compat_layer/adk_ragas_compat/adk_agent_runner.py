"""Run an ADK agent and collect the final answer plus eval session state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from articles_rag_tool import RAGAS_RETRIEVAL_STATE_KEY, RetrievalRecord

RETRIEVAL_TOOL_NAME = "search_articles"


@dataclass
class AgentRunResult:
    user_query: str
    final_response: str
    retrievals: list[RetrievalRecord] = field(default_factory=list)
    events: list[Any] = field(default_factory=list)
    error: str | None = None


def _parse_retrieval_payload(response: Any) -> RetrievalRecord | None:
    if response is None:
        return None
    payload = response
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    if "result" in payload:
        inner = payload["result"]
        if isinstance(inner, str):
            try:
                inner = json.loads(inner)
            except json.JSONDecodeError:
                return None
        payload = inner
    if not isinstance(payload, dict) or "chunks" not in payload:
        return None
    return payload  # type: ignore[return-value]


def _record_key(record: RetrievalRecord) -> tuple[str, tuple[str, ...]]:
    return (record.get("query", ""), tuple(record.get("chunk_ids", [])))


def _merge_retrievals(*sources: list[RetrievalRecord]) -> list[RetrievalRecord]:
    merged: list[RetrievalRecord] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for records in sources:
        for record in records:
            key = _record_key(record)
            if key in seen:
                continue
            seen.add(key)
            merged.append(record)
    return merged


def _retrievals_from_events(events: list[Any]) -> list[RetrievalRecord]:
    from_state: list[RetrievalRecord] = []
    from_tools: list[RetrievalRecord] = []

    for event in events:
        actions = getattr(event, "actions", None)
        if actions and actions.state_delta:
            delta_records = actions.state_delta.get(RAGAS_RETRIEVAL_STATE_KEY)
            if delta_records:
                from_state.extend(list(delta_records))

        for function_response in event.get_function_responses():
            if function_response.name != RETRIEVAL_TOOL_NAME:
                continue
            parsed = _parse_retrieval_payload(function_response.response)
            if parsed:
                from_tools.append(parsed)

    return _merge_retrievals(from_state, from_tools)


def _final_text_from_event(event: Any) -> str:
    if not event.content or not event.content.parts:
        return ""
    return "\n".join(
        part.text
        for part in event.content.parts
        if part.text and not getattr(part, "thought", False)
    )


async def run_agent_with_tools(
    agent: Agent,
    query: str,
    *,
    user_id: str = "eval_user",
) -> AgentRunResult:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=agent.name,
        user_id=user_id,
    )
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name=agent.name,
    )

    result = AgentRunResult(user_query=query, final_response="")

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=Content(parts=[Part(text=query)], role="user"),
        ):
            result.events.append(event)
            print(event)
            if event.is_final_response():
                text = _final_text_from_event(event)
                if text:
                    result.final_response = text
    except Exception as exc:
        result.error = str(exc)

    updated = await session_service.get_session(
        app_name=agent.name,
        user_id=user_id,
        session_id=session.id,
    )
    from_session: list[RetrievalRecord] = []
    if updated:
        from_session = list(updated.state.get(RAGAS_RETRIEVAL_STATE_KEY, []))

    result.retrievals = _merge_retrievals(
        from_session,
        _retrievals_from_events(result.events),
    )
    return result
