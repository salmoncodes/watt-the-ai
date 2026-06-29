"""
metadata_retriever.py
Lookup over the structured DB using extracted fields rather than text meaning.
Good at hard constraints: source, sentiment label, keyword presence. Returns the
underlying text documents so they can be used as grounding context.

Supported filters (all optional):
    source    : "youtube" | "hackernews" | "research"
    sentiment : "positive" | "negative" | "neutral"   (youtube/hackernews only)
    keyword   : substring matched against the document text
                (falls back to the raw query if no keyword filter is given)

Scores are a flat 1.0 (a metadata match is boolean); ordering within each source
uses a natural signal (engagement / sentiment strength / recency).
"""

from rag.config.rag_config import STRUCTURED_DB, TOP_K
from rag.retrieval.base import Retriever, RetrievedDocument, connect


class MetadataRetriever(Retriever):
    name = "metadata"

    def __init__(self, db_path=STRUCTURED_DB):
        self.db_path = db_path

    def retrieve(self, query, top_k=TOP_K, filters=None):
        filters = filters or {}
        source = filters.get("source")
        sentiment = filters.get("sentiment")
        keyword = filters.get("keyword") or (query or None)

        conn = connect(self.db_path)
        try:
            results = []
            if source in (None, "youtube"):
                results += self._youtube(conn, sentiment, keyword, top_k)
            if source in (None, "hackernews"):
                results += self._hackernews(conn, sentiment, keyword, top_k)
            if source in (None, "research"):
                results += self._research(conn, keyword, top_k)
        finally:
            conn.close()
        return results[:top_k]

    def _youtube(self, conn, sentiment, keyword, top_k):
        sql = ("SELECT comment_id AS document_id, video_id, text_clean, "
               "sentiment_label, like_count FROM sentiment_results")
        clauses, params = [], []
        if sentiment:
            clauses.append("sentiment_label = ?"); params.append(sentiment)
        if keyword:
            clauses.append("text_clean LIKE ?"); params.append(f"%{keyword}%")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY like_count DESC LIMIT ?"; params.append(top_k)

        out = []
        for r in conn.execute(sql, params).fetchall():
            out.append(RetrievedDocument(
                document_id=r["document_id"], text=r["text_clean"], score=1.0,
                source="youtube", strategy=self.name, doc_type="comment",
                metadata={"video_id": r["video_id"],
                          "sentiment_label": r["sentiment_label"],
                          "like_count": r["like_count"]}))
        return out

    def _hackernews(self, conn, sentiment, keyword, top_k):
        sql = ("SELECT h.record_id AS document_id, h.story_id, h.text_clean, "
               "hs.sentiment_label, hs.compound FROM hackernews_sentiment_results hs "
               "JOIN hackernews h ON h.record_id = hs.record_id")
        clauses, params = [], []
        if sentiment:
            clauses.append("hs.sentiment_label = ?"); params.append(sentiment)
        if keyword:
            clauses.append("h.text_clean LIKE ?"); params.append(f"%{keyword}%")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY hs.compound DESC LIMIT ?"; params.append(top_k)

        out = []
        for r in conn.execute(sql, params).fetchall():
            out.append(RetrievedDocument(
                document_id=r["document_id"], text=r["text_clean"], score=1.0,
                source="hackernews", strategy=self.name, doc_type="post",
                metadata={"story_id": r["story_id"],
                          "sentiment_label": r["sentiment_label"],
                          "compound": r["compound"]}))
        return out

    def _research(self, conn, keyword, top_k):
        sql = ("SELECT record_id AS document_id, title, venue, text_clean, "
               "published_at FROM research_sources")
        params = []
        if keyword:
            sql += " WHERE text_clean LIKE ?"; params.append(f"%{keyword}%")
        sql += " ORDER BY published_at DESC LIMIT ?"; params.append(top_k)

        out = []
        for r in conn.execute(sql, params).fetchall():
            out.append(RetrievedDocument(
                document_id=r["document_id"], text=r["text_clean"], score=1.0,
                source="research", strategy=self.name, doc_type="abstract",
                metadata={"title": r["title"], "venue": r["venue"],
                          "published_at": r["published_at"]}))
        return out
