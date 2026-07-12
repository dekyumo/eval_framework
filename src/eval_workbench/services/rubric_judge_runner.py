"""Score traces with an ADK LlmAgent and a dynamic rubric output schema."""

from __future__ import annotations

import uuid
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field, create_model

from src.eval_workbench.domain.rubric import Rubric
from src.eval_workbench.domain.trace import Trace
from src.eval_workbench.run_coro_sync import run_coro_sync

_APP_NAME = "eval_workbench"


def format_trace_for_judge(trace: Trace) -> str:
    lines: list[str] = []
    for part in trace.parts:
        role = part.role
        text = part.text or ""
        if part.kind == "media":
            lines.append(f"[{role}]: [attached media {part.media_mime or 'unknown'}]")
        elif part.tool_name and part.kind == "tool_call":
            lines.append(f"[{role}] called tool {part.tool_name} with args {part.tool_args}")
        elif part.tool_response is not None:
            lines.append(f"[tool] response: {part.tool_response}")
        else:
            lines.append(f"[{role}]: {text}")
    return "\n".join(lines)


def _python_type(result_type: str) -> type:
    if result_type == "bool":
        return bool
    if result_type == "int":
        return int
    if result_type == "float":
        return float
    return str


def build_rubric_output_schema(rubric: Rubric) -> type[BaseModel]:
    fields: dict[str, Any] = {}
    for item in rubric.items:
        description = (item.prompt or "").strip() or f"Rubric score for {item.name}"
        if item.type == "enum" and item.enum_values:
            description = f"{description} Allowed values: {', '.join(item.enum_values)}"
        fields[item.name] = (_python_type(item.type), Field(description=description))
    fields["rationale"] = (
        str,
        Field(description="Brief explanation of the assigned scores"),
    )
    model_name = f"RubricScore_{rubric.id.replace(':', '_')}"
    return create_model(model_name, **fields)  # type: ignore[call-overload]


def _judge_instruction(rubric: Rubric) -> str:
    instructions_text = rubric.instructions or ""
    template = rubric.default_judge_prompt or ""
    if "{instructions}" in template:
        grading = template.replace("{instructions}", instructions_text)
    elif template:
        grading = f"{template}\n\nGrading instructions:\n{instructions_text}"
    else:
        grading = instructions_text
    return (
        "Score the provided agent execution trace according to the rubric.\n\n"
        f"{grading}".strip()
    )


async def _run_rubric_judge_async(rubric: Rubric, trace_text: str) -> BaseModel:
    output_schema = build_rubric_output_schema(rubric)
    agent = LlmAgent(
        name="rubric_judge",
        description="Scores agent execution traces against a rubric.",
        instruction=_judge_instruction(rubric),
        output_schema=output_schema,
        model=rubric.judge_model_id or "gemini-2.5-flash",
    )

    user_id = "rubric_judge"
    session_id = f"rubric_judge_{uuid.uuid4().hex[:8]}"
    runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
    await runner.session_service.create_session(
        app_name=_APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=f"Execution trace:\n---\n{trace_text}\n---")],
    )

    final_text = None
    async for event in runner.run_async(
        user_id=user_id,
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
        raise RuntimeError("Rubric judge agent returned no response")

    return output_schema.model_validate_json(final_text)


def judge_trace_with_rubric(rubric: Rubric, trace: Trace) -> BaseModel:
    return run_coro_sync(_run_rubric_judge_async(rubric, format_trace_for_judge(trace)))
