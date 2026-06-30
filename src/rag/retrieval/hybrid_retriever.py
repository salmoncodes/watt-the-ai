"""Hybrid retrieval combines semantic and lexical search results."""

from dataclasses import replace

from rag.config.rag_config import TOP_K, RRF_K, HYBRID_OVERFETCH
from rag.retrieval.base import Retriever
from rag.retrieval.semantic_retriever import SemanticRetriever
from rag.retrieval.lexical_retriever import LexicalRetriever


def reciprocal_rank_fusion(result_lists, k=RRF_K, top_k=TOP_K):
    """Fuse multiple ranked lists of RetrievedDocument into one ranked list."""
    scores, docmap = {}, {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            scores[doc.document_id] = scores.get(doc.document_id, 0.0) + 1.0 / (k + rank + 1)
            docmap.setdefault(doc.document_id, doc)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:top_k]
    return [replace(docmap[doc_id], score=score, strategy="hybrid")
            for doc_id, score in ranked]


class HybridRetriever(Retriever):
    name = "hybrid"

    def __init__(self, semantic=None, lexical=None):
        self.semantic = semantic or SemanticRetriever()
        self.lexical = lexical or LexicalRetriever()

    def retrieve(self, query, top_k=TOP_K, filters=None):
        n = top_k * HYBRID_OVERFETCH
        sem = self.semantic.retrieve(query, top_k=n, filters=filters)
        lex = self.lexical.retrieve(query, top_k=n, filters=filters)
        fused = reciprocal_rank_fusion([sem, lex], top_k=top_k * HYBRID_OVERFETCH)
        return fused[:top_k]
