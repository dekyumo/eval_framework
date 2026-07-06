"""Prepare eval-case input for agents with session state or input_schema."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError
from google.genai import types


def filter_input_payload(agent: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Keep only input_schema keys and validate required fields."""
    input_schema = getattr(agent, "input_schema", None)
    if input_schema is None:
        return payload

    field_names = set(_schema_field_names(input_schema))
    filtered = {key: value for key, value in payload.items() if key in field_names}
    try:
        validated = TypeAdapter(input_schema).validate_python(filtered)
    except ValidationError as exc:
        raise ValueError(f"Agent input does not match input_schema: {exc}") from exc

    if isinstance(validated, BaseModel):
        return validated.model_dump()
    return validated


def build_structured_input_message(payload: dict[str, Any]) -> types.Content:
    """Send structured agent input as JSON text (ADK input_schema convention)."""
    return types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(payload))],
    )


def structured_input_trace_part(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "user",
        "kind": "text",
        "text": json.dumps(payload),
    }


def _schema_field_names(input_schema: Any) -> list[str]:
    if hasattr(input_schema, "model_fields"):
        return list(input_schema.model_fields.keys())
    if isinstance(input_schema, dict) and "properties" in input_schema:
        return list(input_schema["properties"].keys())
    raise TypeError(f"Unsupported input_schema type: {type(input_schema)!r}")
