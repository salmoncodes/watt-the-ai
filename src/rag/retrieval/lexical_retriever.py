"""Lexical retrieval using SQLite FTS5."""

import re
import json

from rag.config.rag_config import VECTOR_DB, VECTOR_TABLES, TABLE_SOURCE, TOP_K
from rag.retrieval.base import Retriever, RetrievedDocument, parse_metadata, connect

_TERM = re.compile(r"[A-Za-z0-9]+")


def _to_match_query(query):
    """Build a safe FTS5 MATCH expression: quote each term, OR them for recall."""
    terms = _TERM.findall(query or "")
    if not terms:
        return None
    return " OR ".join(f'"{t}"' for t in terms)


class LexicalRetriever(Retriever):
    name = "lexical"

    def __init__(self, db_path=VECTOR_DB, tables=VECTOR_TABLES):
        self.db_path = db_path
        self.tables = tables
        self.conn = None
        self._build_index()

    def _build_index(self):
        import sqlite3
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE VIRTUAL TABLE docs USING fts5("
            "document_id UNINDEXED, source UNINDEXED, doc_type UNINDEXED, "
            "metadata UNINDEXED, text)"
        )
        src = connect(self.db_path)
        try:
            for table in self.tables:
                source = TABLE_SOURCE.get(table, table)
                rows = src.execute(
                    f"SELECT document_id, doc_type, text, metadata FROM {table}"
                ).fetchall()
                self.conn.executemany(
                    "INSERT INTO docs (document_id, source, doc_type, metadata, text) "
                    "VALUES (?,?,?,?,?)",
                    [(r["document_id"], source, r["doc_type"], r["metadata"], r["text"] or "")
                     for r in rows],
                )
        finally:
            src.close()
        self.conn.commit()

    def retrieve(self, query, top_k=TOP_K, filters=None):
        match = _to_match_query(query)
        if not match:
            return []
        source_filter = (filters or {}).get("source")
        if source_filter:
            rows = self.conn.execute(
                "SELECT document_id, source, doc_type, metadata, text, bm25(docs) AS rank "
                "FROM docs WHERE docs MATCH ? AND source = ? ORDER BY rank LIMIT ?",
                (match, source_filter, top_k * 4),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT document_id, source, doc_type, metadata, text, bm25(docs) AS rank "
                "FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?",
                (match, top_k * 4),
            ).fetchall()

        results = []
        for r in rows:
            results.append(RetrievedDocument(
                document_id=r["document_id"],
                text=r["text"],
                score=-float(r["rank"]),       # negate: higher = better
                source=r["source"],
                strategy=self.name,
                doc_type=r["doc_type"],
                metadata=parse_metadata(r["metadata"]),
            ))
        return results[:top_k]
