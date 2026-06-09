"""
transfer_to_vector.py

Builds the vector database and directly generates embeddings for:
- comments
- transcript chunks
- video metadata

This is a single-step ingestion pipeline:
text -> embedding -> vector_db

No separate embedding stage is required.
"""

import sqlite3
import json
from pathlib import Path

from database.utils.io_utils import load_json

from sentence_transformers import SentenceTransformer


DB_PATH = Path("database/vector_db/vector.db")
SCHEMA_PATH = Path("database/vector_db/vector_schema.sql")


# ----------------------------
# MODEL LOADING
# ----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")


# ----------------------------
# DB INIT
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    conn.commit()
    return conn


# ----------------------------
# EMBEDDING HELPER
# ----------------------------
def embed(text):
    if not text:
        return None
    return model.encode(text).tolist()


# ----------------------------
# DOCUMENT BUILDERS
# ----------------------------
def build_comment_docs(comments):
    docs = []
    for c in comments:
        text = c.get("text_original", "")
        docs.append({
            "document_id": f"c_{c.get('comment_id')}",
            "video_id": c.get("video_id"),
            "doc_type": "comment",
            "text": text,
            "metadata": {
                "like_count": c.get("like_count"),
                "author": c.get("author_display_name"),
                "published_at": c.get("published_at"),
                "parent_id": c.get("parent_id"),
                "comment_type": c.get("comment_type")
            },
            "embedding": embed(text)
        })
    return docs


def build_transcript_docs(transcripts):
    docs = []
    for t in transcripts:
        text = t.get("text", "")
        if not text:
            continue

        docs.append({
            "document_id": f"t_{t.get('video_id')}",
            "video_id": t.get("video_id"),
            "doc_type": "transcript",
            "text": text,
            "metadata": {
                "status": t.get("status"),
                "language_attempted": t.get("language_attempted")
            },
            "embedding": embed(text)
        })
    return docs


def build_video_docs(videos):
    docs = []
    for v in videos:
        text = f"{v.get('title','')} {v.get('description','')}"

        docs.append({
            "document_id": f"v_{v.get('video_id')}",
            "video_id": v.get("video_id"),
            "doc_type": "video_summary",
            "text": text,
            "metadata": {
                "channel_title": v.get("channel_title"),
                "published_at": v.get("published_at"),
                "view_count": v.get("view_count"),
                "like_count": v.get("like_count"),
                "comment_count": v.get("comment_count"),
                "tags": v.get("tags", [])
            },
            "embedding": embed(text)
        })
    return docs


# ----------------------------
# INSERT INTO VECTOR DB
# ----------------------------
def insert_documents(conn, docs):
    cursor = conn.cursor()

    for d in docs:
        cursor.execute("""
            INSERT OR REPLACE INTO documents
            (document_id, video_id, doc_type, text, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            d.get("document_id"),
            d.get("video_id"),
            d.get("doc_type"),
            d.get("text"),
            json.dumps(d.get("metadata", {}), ensure_ascii=False),
            json.dumps(d.get("embedding")) if d.get("embedding") else None
        ))

    conn.commit()


# ----------------------------
# MAIN PIPELINE
# ----------------------------
def main():
    conn = init_db()

    comments = load_json("data/preprocessing/clean_comments.json")
    transcripts = load_json("data/preprocessing/clean_transcripts.json")
    videos = load_json("data/preprocessing/clean_videos.json")

    comment_docs = build_comment_docs(comments)
    transcript_docs = build_transcript_docs(transcripts)
    video_docs = build_video_docs(videos)

    all_docs = comment_docs + transcript_docs + video_docs

    insert_documents(conn, all_docs)

    conn.close()

    print(f"Vector DB created with {len(all_docs)} embedded documents.")


if __name__ == "__main__":
    main()
