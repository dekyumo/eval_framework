"""Convert ADK agent runs into Ragas SingleTurnSample objects."""

from __future__ import annotations

import json

from ragas_import_fix import apply_ragas_import_fix

apply_ragas_import_fix()

from ragas.dataset_schema import SingleTurnSample
from ragas.messages import AIMessage, HumanMessage, ToolCall, ToolMessage

from .adk_agent_runner import AgentRunResult


def agent_run_to_messages(run: AgentRunResult) -> list[HumanMessage | AIMessage | ToolMessage]:
    messages: list[HumanMessage | AIMessage | ToolMessage] = [
        HumanMessage(content=run.user_query),
    ]

    for record in run.retrievals:
        messages.append(
            AIMessage(
                content="",
                tool_calls=[
                    ToolCall(name="search_articles", args={"query": record["query"]})
                ],
            )
        )
        messages.append(ToolMessage(content=json.dumps(record, indent=2)))

    if run.final_response:
        messages.append(AIMessage(content=run.final_response))

    return messages


def agent_run_to_single_turn_sample(
    run: AgentRunResult,
    *,
    reference: str | None = None,
    reference_contexts: list[str] | None = None,
    reference_context_ids: list[str | int] | None = None,
) -> SingleTurnSample:
    retrieved_contexts: list[str] = []
    retrieved_context_ids: list[str] = []

    for record in run.retrievals:
        for chunk in record.get("chunks", []):
            retrieved_contexts.append(chunk["text"])
            retrieved_context_ids.append(chunk["chunk_id"])
        for chunk_id in record.get("chunk_ids", []):
            if chunk_id not in retrieved_context_ids:
                retrieved_context_ids.append(chunk_id)

    return SingleTurnSample(
        user_input=run.user_query,
        retrieved_contexts=retrieved_contexts or None,
        retrieved_context_ids=retrieved_context_ids or None,
        response=run.final_response,
        reference=reference,
        reference_contexts=reference_contexts,
        reference_context_ids=reference_context_ids,
    )


def pretty_print_messages(messages: list[HumanMessage | AIMessage | ToolMessage]) -> None:
    for message in messages:
        print(message.pretty_repr())
        print()
