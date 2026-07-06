"""Aggregate token usage from ADK runner events."""

from __future__ import annotations

from typing import Any


def empty_token_totals() -> dict[str, int]:
    return {"prompt": 0, "completion": 0, "total": 0}


def accumulate_token_usage(totals: dict[str, int], event: Any) -> None:
    """Sum prompt/completion tokens from an event's usage_metadata."""
    usage = getattr(event, "usage_metadata", None)
    if not usage:
        return

    prompt = int(getattr(usage, "prompt_token_count", None) or 0)
    completion = int(getattr(usage, "candidates_token_count", None) or 0)
    totals["prompt"] += prompt
    totals["completion"] += completion
    totals["total"] = totals["prompt"] + totals["completion"]


def append_trace_parts_from_event(event: Any, trace_parts: list[dict[str, Any]]) -> None:
    """Record tool calls/responses and final assistant text from one ADK event."""
    if event.message:
        for part in event.message.parts:
            if part.function_call:
                trace_parts.append({
                    "role": "assistant",
                    "kind": "tool_call",
                    "tool_name": part.function_call.name,
                    "tool_args": part.function_call.args,
                })
            if part.function_response:
                trace_parts.append({
                    "role": "tool",
                    "kind": "tool_response",
                    "tool_name": part.function_response.name,
                    "tool_response": part.function_response.response,
                })

    if event.is_final_response() and event.message:
        text_parts = [
            part.text
            for part in event.message.parts
            if part.text
        ]
        final_text = "".join(text_parts)
        if final_text:
            trace_parts.append({
                "role": "assistant",
                "kind": "text",
                "text": final_text,
            })
