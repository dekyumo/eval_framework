"""Ragas judge LLM backed by a minimal ADK agent with structured output."""

from __future__ import annotations

import asyncio
from typing import TypeVar

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.utils._schema_utils import validate_schema
from google.genai.types import Content, Part
from pydantic import BaseModel

from ragas_import_fix import apply_ragas_import_fix

apply_ragas_import_fix()

from ragas.llms.base import InstructorBaseRagasLLM

T = TypeVar("T", bound=BaseModel)


class ADKRagasLLM(InstructorBaseRagasLLM):
    """Runs Ragas structured prompts through a throwaway ADK agent.

    Each call spins up an agent with ``output_schema=<pydantic model>`` so the
    Gemini response is validated by ADK (ADK 2.x names this ``output_schema``).
    """

    is_async = True

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self.model = model
        self._session_service = InMemorySessionService()

    async def _run_structured(
        self, prompt: str, response_model: type[T]
    ) -> T:
        agent = Agent(
            name="ragas_judge",
            model=self.model,
            description="Structured evaluator for Ragas metrics.",
            instruction="Evaluate the user message and return structured output.",
            output_schema=response_model,
        )
        session = await self._session_service.create_session(
            app_name=agent.name,
            user_id="ragas_judge",
        )
        runner = Runner(
            agent=agent,
            session_service=self._session_service,
            app_name=agent.name,
        )

        async for event in runner.run_async(
            user_id="ragas_judge",
            session_id=session.id,
            new_message=Content(parts=[Part(text=prompt)], role="user"),
        ):
            if not event.is_final_response() or not event.content or not event.content.parts:
                continue
            text = "".join(
                part.text for part in event.content.parts if part.text and not part.thought
            )
            if not text.strip():
                continue
            validated = validate_schema(response_model, text)
            return response_model.model_validate(validated)

        raise RuntimeError("ADK judge agent produced no structured response")

    async def agenerate(self, prompt: str, response_model: type[T]) -> T:
        return await self._run_structured(prompt, response_model)

    def generate(self, prompt: str, response_model: type[T]) -> T:
        return asyncio.run(self.agenerate(prompt, response_model))
