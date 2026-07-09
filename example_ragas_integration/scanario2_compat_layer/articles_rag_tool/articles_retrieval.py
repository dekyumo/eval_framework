"""LlamaIndex retrieval tool that indexes in-memory news articles."""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from google.adk.tools.retrieval.llama_index_retrieval import LlamaIndexRetrieval
from google.adk.tools.tool_context import ToolContext
from llama_index.core.base.base_retriever import BaseRetriever
from typing_extensions import override

from pydantic import BaseModel
from dataclasses import dataclass

from .keyword_articles_retriever import KeywordArticlesRetriever

logger = logging.getLogger("google_adk." + __name__)

RAGAS_RETRIEVAL_STATE_KEY = "ragas_retrievals"

@dataclass
class RetrievalChunk(BaseModel):
    chunk_id: str
    doc_id: str
    score: float | None
    category: str | None
    article_index: int | None
    text: str

@dataclass
class RetrievalRecord(BaseModel):
    query: str
    chunk_ids: list[str]
    chunks: list[RetrievalChunk]

class ArticlesRetrieval(LlamaIndexRetrieval):
    """Build a LlamaIndex retriever from article dicts instead of a folder of files."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        articles: list[dict[str, str]],
        similarity_top_k: int = 3,
        retriever: BaseRetriever | None = None,
    ):
        self.articles = articles
        self.similarity_top_k = similarity_top_k
        if retriever is None:
            retriever = KeywordArticlesRetriever.from_articles(
                articles,
                similarity_top_k=similarity_top_k,
            )
        super().__init__(name=name, description=description, retriever=retriever)

    @override
    async def run_async(
        self, *, args: dict[str, Any], tool_context: ToolContext
    ) -> str:
        query = args["query"]
        nodes = self.retriever.retrieve(query)
        chunks = []
        chunk_ids: list[str] = []

        for node_with_score in nodes:
            node = node_with_score.node
            chunk_id = node.node_id
            chunk_ids.append(chunk_id)
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": node.ref_doc_id or node.node_id,
                    "score": node_with_score.score,
                    "category": node.metadata.get("category"),
                    "article_index": node.metadata.get("article_index"),
                    "text": node.get_content(),
                }
            )

        record: RetrievalRecord = {
            "query": query,
            "chunk_ids": chunk_ids,
            "chunks": chunks,
        }

        existing = list(tool_context.state.get(RAGAS_RETRIEVAL_STATE_KEY, []))
        #existing.append(record)
        tool_context.state[RAGAS_RETRIEVAL_STATE_KEY] = existing + [record]

        print("new state:", tool_context.state[RAGAS_RETRIEVAL_STATE_KEY])
        return json.dumps(record, indent=2)
