"""End-to-end demo: ADK RAG agent -> Ragas SingleTurnSample -> context recall metrics."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is importable when launched as a script from any cwd.
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from google.adk.agents import Agent

from adk_ragas_compat import (
    ADKRagasLLM,
    AgentRunResult,
    agent_run_to_messages,
    agent_run_to_single_turn_sample,
    pretty_print_messages,
    run_agent_with_tools,
)
from articles_rag_tool import (
    ARTICLES,
    DEMO_QUERY,
    DEMO_REFERENCE,
    DEMO_REFERENCE_CONTEXT,
    DEMO_REFERENCE_CONTEXT_ID,
    ArticlesRetrieval,
)
from ragas_import_fix import apply_ragas_import_fix

apply_ragas_import_fix()

from ragas.dataset_schema import SingleTurnSample
from ragas.llms.base import InstructorBaseRagasLLM
from ragas.metrics._context_recall import (
    IDBasedContextRecall,
    LLMContextRecall,
    NonLLMContextRecall,
)
from ragas.metrics._string import DistanceMeasure


def build_news_agent() -> Agent:
    return Agent(
        name="news_qa_agent",
        model="gemini-2.5-flash",
        description="Answers questions using retrieved news articles.",
        instruction=(
            "You answer questions about news articles.\n"
            "1. Always call search_articles first for factual questions.\n"
            "2. Base your answer only on retrieved article text.\n"
            "3. Keep answers concise (1-2 sentences)."
        ),
        tools=[
            ArticlesRetrieval(
                name="search_articles",
                description=(
                    "Search indexed news articles about business, health, technology, "
                    "and science. Always call this before answering factual questions."
                ),
                articles=ARTICLES,
                similarity_top_k=3,
            )
        ],
    )

async def score_all_context_recalls(
    sample: SingleTurnSample,
    llm: InstructorBaseRagasLLM | None = None,
) -> dict[str, float]:
    scores: dict[str, float] = {}

    id_metric = IDBasedContextRecall()
    scores["id_based_context_recall"] = await id_metric.single_turn_ascore(sample)

    try:
        for measure in DistanceMeasure:
            non_llm = NonLLMContextRecall()
            non_llm.distance_measure = measure
            scores[f"non_llm_context_recall[{measure.value}]"] = (
                await non_llm.single_turn_ascore(sample)
            )
    except ImportError as exc:
        scores["non_llm_context_recall"] = float("nan")
        print(f"Skipping NonLLMContextRecall: {exc}")

    if llm is not None:
        llm_metric = LLMContextRecall()
        llm_metric.llm = llm
        scores["llm_context_recall"] = await llm_metric.single_turn_ascore(sample)

    return scores


async def main() -> None:
    judge_llm = ADKRagasLLM(model="gemini-2.5-flash")
    agent = build_news_agent()
    print(f"Running ADK agent with query:\n  {DEMO_QUERY}\n")
    run = await run_agent_with_tools(agent, DEMO_QUERY)

    if run.error:
        print(f"Agent error: {run.error}\n")

    print("Retrievals:")
    if not run.retrievals:
        print("  (none — check GEMINI_API_KEY, SSL certs, or agent logs above)")
    for record in run.retrievals:
        print(f"  - query={record['query']!r}, chunks={record['chunk_ids']}")
    print(f"\nFinal response:\n{run.final_response or '(empty)'}\n")

    if not run.retrievals:
        print(
            "Hint: session state keys must not use the temp: prefix; "
            "ADK drops them when committing events. Use ragas_retrievals."
        )
        return

    print("Ragas message trace:")
    pretty_print_messages(agent_run_to_messages(run))

    sample = agent_run_to_single_turn_sample(
        run,
        reference=DEMO_REFERENCE,
        reference_contexts=[DEMO_REFERENCE_CONTEXT],
        reference_context_ids=[DEMO_REFERENCE_CONTEXT_ID],
    )
    print("SingleTurnSample:")
    print(sample.to_string())

    scores = await score_all_context_recalls(sample, llm=judge_llm)
    print("\nContext recall scores:")
    for name, value in scores.items():
        if value != value:
            print(f"  {name}: (skipped)")
        else:
            print(f"  {name}: {value:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
