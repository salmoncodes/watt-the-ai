"""
transfer_to_structured.py

Transfers cleaned data + feature extraction outputs into a structured SQLite database.

This module handles:
- Loading processed JSON files
- Mapping them into relational tables
- Inserting data into structured SQLite DB
"""

import sqlite3
from pathlib import Path

from database.utils.io_utils import load_json


DB_PATH = Path("database/structured_db/structured.db")
SCHEMA_PATH = Path("database/structured_db/structured_schema.sql")


# ----------------------------
# DB INITIALIZATION
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        cursor.executescript(file.read())

    conn.commit()
    return conn


# ----------------------------
# INSERT HELPERS
# ----------------------------
def insert_videos(conn, videos):
    cursor = conn.cursor()
    for v in videos:
        cursor.execute("""
            INSERT OR REPLACE INTO videos VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            v.get("video_id"),
            v.get("title"),
            v.get("description"),
            v.get("channel_id"),
            v.get("channel_title"),
            v.get("published_at"),
            str(v.get("tags", [])),
            v.get("category_id"),
            v.get("duration"),
            v.get("caption"),
            v.get("view_count"),
            v.get("like_count"),
            v.get("comment_count"),
        ))
    conn.commit()


def insert_comments(conn, comments):
    cursor = conn.cursor()
    for c in comments:
        cursor.execute("""
            INSERT OR REPLACE INTO comments VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            c.get("comment_id"),
            c.get("video_id"),
            c.get("parent_id"),
            c.get("author_display_name"),
            c.get("text_original"),
            c.get("like_count"),
            c.get("published_at"),
            c.get("updated_at"),
            c.get("total_reply_count"),
            1 if c.get("is_public", True) else 0,
            c.get("comment_type"),
        ))
    conn.commit()


def insert_transcripts(conn, transcripts):
    cursor = conn.cursor()
    for t in transcripts:
        # segments are flattened into single text for structured DB
        cursor.execute("""
            INSERT OR REPLACE INTO transcripts VALUES (?,?,?,?,?,?,?)
        """, (
            t.get("video_id"),
            t.get("video_id") + "_t",
            t.get("text"),
            t.get("status"),
            str(t.get("language_attempted")),
            None,
            None,
        ))
    conn.commit()


# ----------------------------
# FEATURE TABLE INSERTS
# ----------------------------
def insert_sentiment(conn, sentiment_data):
    cursor = conn.cursor()
    for s in sentiment_data:
        cursor.execute("""
            INSERT INTO sentiment_results VALUES (NULL,?,?,?,?,?,?,?,?)
        """, (
            s.get("video_id"),
            s.get("document_id"),
            s.get("doc_type"),
            s.get("negative"),
            s.get("neutral"),
            s.get("positive"),
            s.get("compound"),
            s.get("label"),
        ))
    conn.commit()


def insert_ner(conn, ner_data):
    cursor = conn.cursor()
    for n in ner_data:
        cursor.execute("""
            INSERT INTO ner_results VALUES (NULL,?,?,?,?,?)
        """, (
            n.get("video_id"),
            n.get("document_id"),
            n.get("entity"),
            n.get("entity_label"),
            n.get("doc_type"),
        ))
    conn.commit()


def insert_keywords(conn, keyword_data):
    cursor = conn.cursor()
    for k in keyword_data:
        cursor.execute("""
            INSERT INTO keyword_results VALUES (NULL,?,?,?,?,?)
        """, (
            k.get("video_id"),
            k.get("document_id"),
            k.get("keyword"),
            k.get("score"),
            k.get("doc_type"),
        ))
    conn.commit()


def insert_topics(conn, topic_data):
    cursor = conn.cursor()
    for t in topic_data:
        cursor.execute("""
            INSERT INTO topic_results VALUES (NULL,?,?,?,?,?)
        """, (
            t.get("video_id"),
            t.get("document_id"),
            t.get("topic_id"),
            t.get("topic_score"),
            t.get("doc_type"),
        ))
    conn.commit()


# ----------------------------
# MAIN PIPELINE
# ----------------------------
def main():
    conn = init_db()

    # Load structured inputs
    videos = load_json("data/preprocessing/clean_videos.json")
    comments = load_json("data/preprocessing/clean_comments.json")
    transcripts = load_json("data/preprocessing/clean_transcripts.json")

    sentiment = load_json("data/feature_extraction/sentiment_results.json")
    ner = load_json("data/feature_extraction/ner_results.json")
    keywords = load_json("data/feature_extraction/keyword_results.json")
    topics = load_json("data/feature_extraction/topic_results.json")

    # Insert into DB
    insert_videos(conn, videos)
    insert_comments(conn, comments)
    insert_transcripts(conn, transcripts)

    insert_sentiment(conn, sentiment)
    insert_ner(conn, ner)
    insert_keywords(conn, keywords)
    insert_topics(conn, topics)

    conn.close()
    print("Structured database population complete.")


if __name__ == "__main__":
    main()
