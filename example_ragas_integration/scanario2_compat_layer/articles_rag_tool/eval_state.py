"""Shared session-state keys for Ragas evaluation."""

from __future__ import annotations

from typing import Any, TypedDict

RAGAS_RETRIEVAL_STATE_KEY = "temp:ragas_retrievals"


class RetrievalChunk(TypedDict):
    chunk_id: str
    doc_id: str
    score: float | None
    category: str | None
    article_index: int | None
    text: str


class RetrievalRecord(TypedDict):
    query: str
    chunk_ids: list[str]
    chunks: list[RetrievalChunk]


