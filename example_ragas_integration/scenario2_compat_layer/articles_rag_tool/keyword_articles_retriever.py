"""Keyword retriever for in-memory articles (no embedding API calls)."""

from __future__ import annotations

import re

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.schema import BaseNode, NodeWithScore, QueryBundle, TextNode


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


class KeywordArticlesRetriever(BaseRetriever):
    """Simple keyword-overlap retriever backed by LlamaIndex nodes."""

    def __init__(
        self,
        nodes: list[BaseNode],
        similarity_top_k: int = 3,
        callback_manager: CallbackManager | None = None,
    ) -> None:
        self._nodes = nodes
        self._similarity_top_k = similarity_top_k
        super().__init__(callback_manager=callback_manager)

    @classmethod
    def from_articles(
        cls,
        articles: list[dict[str, str]],
        *,
        similarity_top_k: int = 3,
    ) -> KeywordArticlesRetriever:
        nodes: list[BaseNode] = []
        for index, article in enumerate(articles):
            nodes.append(
                TextNode(
                    text=article["text"],
                    id_=f"article-{index}",
                    metadata={
                        "category": article["category"],
                        "article_index": index,
                    },
                )
            )
        return cls(nodes=nodes, similarity_top_k=similarity_top_k)

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        query_terms = _tokenize(query_bundle.query_str)
        scored: list[tuple[float, BaseNode]] = []

        for node in self._nodes:
            text_terms = _tokenize(node.get_content())
            if not query_terms:
                continue
            overlap = len(query_terms & text_terms)
            if overlap == 0:
                continue
            score = overlap / len(query_terms)
            scored.append((score, node))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            NodeWithScore(node=node, score=score)
            for score, node in scored[: self._similarity_top_k]
        ]
