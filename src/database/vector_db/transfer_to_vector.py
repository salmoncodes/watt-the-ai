"""
transfer_to_vector.py

Builds the vector database and generates embeddings for the chunked documents
produced by chunking.py, across all three sources:
- YouTube   (comments, transcript chunks, video summaries)
- HackerNews (posts / text chunks)
- Research  (abstract chunks)

Pipeline:  chunked JSONL -> embedding -> vector_db

This step consumes chunking.py's output (the *_documents.jsonl files) rather than
re-deriving documents from the cleaned JSON, so chunking decides how text is
split. Run chunking.py before this script.
"""

import json
import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database.utils.io_utils import load_jsonl
from rag.config.rag_config import EMBEDDING_MODEL

from sentence_transformers import SentenceTransformer


# ----------------------------
# PATHS
# ----------------------------
DB_PATH = Path("src/database/vector_db/vector.db")
SCHEMA_PATH = Path("src/database/vector_db/vector_schema.sql")
CHUNK_DIR = Path("src/database/vector_db/chunks")


# ----------------------------
# MODEL LOADING
# ----------------------------
model = SentenceTransformer(EMBEDDING_MODEL)


# ----------------------------
# DB INIT
# ----------------------------
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():          # rebuild from scratch
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


# ----------------------------
# EMBEDDING HELPER
# ----------------------------
def embed_texts(texts):
    """Batch-encode a list of texts into a list of vectors (as plain lists).
    Empty input returns an empty list."""
    if not texts:
        return []
    return model.encode(texts, show_progress_bar=False).tolist()


# ----------------------------
# INSERT INTO VECTOR DB (one function per source table)
# ----------------------------
def insert_youtube(conn, docs):
    cur = conn.cursor()
    embeddings = embed_texts([d.get("text", "") for d in docs])
    for d, emb in zip(docs, embeddings):
        cur.execute("""
            INSERT OR REPLACE INTO youtube_documents
            (document_id, video_id, doc_type, text, metadata, embedding)
            VALUES (?,?,?,?,?,?)
        """, (
            d.get("document_id"),
            d.get("video_id"),
            d.get("doc_type"),
            d.get("text"),
            json.dumps(d.get("metadata", {}), ensure_ascii=False),
            json.dumps(emb),
        ))
    conn.commit()


def insert_hackernews(conn, docs):
    cur = conn.cursor()
    embeddings = embed_texts([d.get("text", "") for d in docs])
    for d, emb in zip(docs, embeddings):
        cur.execute("""
            INSERT OR REPLACE INTO hackernews_documents
            (document_id, record_id, story_id, doc_type, text, metadata, embedding)
            VALUES (?,?,?,?,?,?,?)
        """, (
            d.get("document_id"),
            d.get("record_id"),
            d.get("story_id"),
            d.get("doc_type"),
            d.get("text"),
            json.dumps(d.get("metadata", {}), ensure_ascii=False),
            json.dumps(emb),
        ))
    conn.commit()


def insert_research(conn, docs):
    cur = conn.cursor()
    embeddings = embed_texts([d.get("text", "") for d in docs])
    for d, emb in zip(docs, embeddings):
        cur.execute("""
            INSERT OR REPLACE INTO research_documents
            (document_id, record_id, doi, doc_type, text, metadata, embedding)
            VALUES (?,?,?,?,?,?,?)
        """, (
            d.get("document_id"),
            d.get("record_id"),
            d.get("doi"),
            d.get("doc_type"),
            d.get("text"),
            json.dumps(d.get("metadata", {}), ensure_ascii=False),
            json.dumps(emb),
        ))
    conn.commit()


# ----------------------------
# MAIN PIPELINE
# ----------------------------
def main():
    conn = init_db()

    youtube = load_jsonl(CHUNK_DIR / "youtube_documents.jsonl")
    hackernews = load_jsonl(CHUNK_DIR / "hackernews_documents.jsonl")
    research = load_jsonl(CHUNK_DIR / "research_documents.jsonl")

    insert_youtube(conn, youtube)
    insert_hackernews(conn, hackernews)
    insert_research(conn, research)

    total = len(youtube) + len(hackernews) + len(research)
    conn.close()

    print(f"Vector DB created with {total} embedded documents "
          f"(youtube={len(youtube)}, hackernews={len(hackernews)}, research={len(research)}).")


if __name__ == "__main__":
    main()
