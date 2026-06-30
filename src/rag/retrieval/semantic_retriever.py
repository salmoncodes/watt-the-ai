"""Semantic retrieval using stored embeddings."""

import json

import numpy as np

from rag.config.rag_config import VECTOR_DB, VECTOR_TABLES, TABLE_SOURCE, TOP_K
from rag.representation.embedder import embed_query
from rag.retrieval.base import Retriever, RetrievedDocument, parse_metadata, connect


class SemanticRetriever(Retriever):
    name = "semantic"

    def __init__(self, db_path=VECTOR_DB, tables=VECTOR_TABLES):
        self.db_path = db_path
        self.tables = tables

    def _tables_for_source(self, source_filter):
        if not source_filter:
            return self.tables
        return [table for table in self.tables
                if TABLE_SOURCE.get(table, table) == source_filter]

    def _load_corpus(self, source_filter=None):
        """Return (matrix, docs) where matrix is (n, dim) of embeddings."""
        vectors, docs = [], []
        conn = connect(self.db_path)
        try:
            for table in self._tables_for_source(source_filter):
                source = TABLE_SOURCE.get(table, table)
                rows = conn.execute(
                    f"SELECT document_id, doc_type, text, metadata, embedding FROM {table}"
                ).fetchall()
                for r in rows:
                    if not r["embedding"]:
                        continue
                    vectors.append(json.loads(r["embedding"]))
                    docs.append((r, source))
        finally:
            conn.close()
        if not vectors:
            return np.empty((0, 0)), []
        return np.array(vectors, dtype=float), docs

    def search_by_vector(self, query_vector, top_k=TOP_K, source_filter=None):
        """Rank stored documents against an already-computed query vector.
        Kept separate from retrieve() so it can be used (and tested) without the
        embedding model."""
        if query_vector is None:
            return []
        matrix, docs = self._load_corpus(source_filter)
        if len(docs) == 0:
            return []

        q = np.array(query_vector, dtype=float)
        denom = (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q))
        denom[denom == 0] = 1e-12
        scores = (matrix @ q) / denom

        order = np.argsort(-scores)[:top_k]
        results = []
        for i in order:
            row, source = docs[i]
            results.append(RetrievedDocument(
                document_id=row["document_id"],
                text=row["text"],
                score=float(scores[i]),
                source=source,
                strategy=self.name,
                doc_type=row["doc_type"],
                metadata=parse_metadata(row["metadata"]),
            ))
        return results

    def retrieve(self, query, top_k=TOP_K, filters=None):
        source_filter = (filters or {}).get("source")
        return self.search_by_vector(
            embed_query(query),
            top_k=top_k,
            source_filter=source_filter,
        )[:top_k]
