"""Metadata retrieval from the structured database."""

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
        relation_contains = filters.get("relation_contains")
        keyword = filters.get("keyword")

        conn = connect(self.db_path)
        try:
            if relation_contains:
                return self._relations(conn, source, relation_contains, top_k)

            results = []
            if source in (None, "youtube"):
                results += self._youtube(conn, sentiment, keyword, top_k)
            if source in (None, "hackernews"):
                results += self._hackernews(conn, sentiment, keyword, top_k)
            if source in (None, "research") and not sentiment:
                results += self._research(conn, keyword, top_k)
        finally:
            conn.close()
        if source:
            return results[:top_k]
        return self._mix_sources(results, top_k)

    def _mix_sources(self, results, top_k):
        grouped = {}
        for item in results:
            grouped.setdefault(item.source, []).append(item)

        mixed = []
        while len(mixed) < top_k and any(grouped.values()):
            for source in ["youtube", "hackernews", "research"]:
                if grouped.get(source):
                    mixed.append(grouped[source].pop(0))
                    if len(mixed) >= top_k:
                        break
        return mixed

    def _relations(self, conn, source, relation_contains, top_k):
        like = f"%{relation_contains}%"
        results = []

        if source in (None, "youtube"):
            rows = conn.execute("""
                SELECT rr.document_id, rr.video_id, rr.text_clean,
                       r.subject_text, r.relation, r.object_text, r.relation_text
                FROM youtube_relation_results rr
                JOIN youtube_relations r ON r.relation_result_id = rr.id
                WHERE r.relation LIKE ?
                   OR r.subject_text LIKE ?
                   OR r.object_text LIKE ?
                   OR r.relation_text LIKE ?
                LIMIT ?
            """, (like, like, like, like, top_k)).fetchall()
            for r in rows:
                results.append(RetrievedDocument(
                    document_id=r["document_id"], text=r["text_clean"], score=1.0,
                    source="youtube", strategy=self.name, doc_type="relation",
                    metadata={"video_id": r["video_id"], "relation": r["relation"],
                              "subject": r["subject_text"], "object": r["object_text"],
                              "relation_text": r["relation_text"]}))

        if source in (None, "hackernews") and len(results) < top_k:
            rows = conn.execute("""
                SELECT rr.record_id, rr.story_id, rr.text_clean,
                       r.subject_text, r.relation, r.object_text, r.relation_text
                FROM hackernews_relation_results rr
                JOIN hackernews_relations r ON r.relation_result_id = rr.id
                WHERE r.relation LIKE ?
                   OR r.subject_text LIKE ?
                   OR r.object_text LIKE ?
                   OR r.relation_text LIKE ?
                LIMIT ?
            """, (like, like, like, like, top_k - len(results))).fetchall()
            for r in rows:
                results.append(RetrievedDocument(
                    document_id=r["record_id"], text=r["text_clean"], score=1.0,
                    source="hackernews", strategy=self.name, doc_type="relation",
                    metadata={"story_id": r["story_id"], "relation": r["relation"],
                              "subject": r["subject_text"], "object": r["object_text"],
                              "relation_text": r["relation_text"]}))

        if source in (None, "research") and len(results) < top_k:
            rows = conn.execute("""
                SELECT rr.record_id, rr.doi, rr.title, rr.text_clean,
                       r.subject_text, r.relation, r.object_text, r.relation_text
                FROM research_relation_results rr
                JOIN research_relations r ON r.relation_result_id = rr.id
                WHERE r.relation LIKE ?
                   OR r.subject_text LIKE ?
                   OR r.object_text LIKE ?
                   OR r.relation_text LIKE ?
                LIMIT ?
            """, (like, like, like, like, top_k - len(results))).fetchall()
            for r in rows:
                results.append(RetrievedDocument(
                    document_id=r["record_id"], text=r["text_clean"], score=1.0,
                    source="research", strategy=self.name, doc_type="relation",
                    metadata={"doi": r["doi"], "title": r["title"],
                              "relation": r["relation"], "subject": r["subject_text"],
                              "object": r["object_text"],
                              "relation_text": r["relation_text"]}))

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
