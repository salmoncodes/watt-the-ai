"""
transfer_to_structured.py

Transfers cleaned data + feature-extraction outputs into the structured SQLite
database.

This module handles:
- Loading processed JSON files
- Mapping them into relational tables (including child tables for nested arrays)
- Inserting data into the structured SQLite DB

Insert order respects foreign keys: each source's core table is populated before
its analysis tables, and every header row is inserted before its child rows.
"""

import sys
import sqlite3
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database.utils.io_utils import load_json


# ----------------------------
# PATHS
# ----------------------------
DB_PATH = Path("src/database/structured_db/structured.db")
SCHEMA_PATH = Path("src/database/structured_db/structured_schema.sql")

PREP = Path("data/preprocessing")
FEAT = Path("data/feature_extraction")


# ----------------------------
# DB INITIALIZATION
# ----------------------------
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():          # rebuild from scratch
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        conn.executescript(file.read())
    conn.commit()
    return conn


def row_exists(conn, table, column, value):
    row = conn.execute(
        f"SELECT 1 FROM {table} WHERE {column} = ? LIMIT 1",
        (value,),
    ).fetchone()
    return row is not None


# ============================================================================
# YOUTUBE
# ============================================================================
def insert_videos(conn, videos):
    cur = conn.cursor()
    for v in videos:
        cur.execute("INSERT OR REPLACE INTO videos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            v.get("video_id"),
            v.get("title_original"),
            v.get("title_clean"),
            v.get("description_original"),
            v.get("description_clean"),
            v.get("channel_id"),
            v.get("channel_title"),
            v.get("published_at"),
            v.get("category_id"),
            v.get("duration"),
            v.get("caption"),
            v.get("view_count"),
            v.get("like_count"),
            v.get("comment_count"),
        ))
        for tag in (v.get("tags") or []):
            cur.execute("INSERT INTO video_tags (video_id, tag) VALUES (?,?)",
                        (v.get("video_id"), tag))
    conn.commit()


def insert_comments(conn, comments):
    cur = conn.cursor()
    for c in comments:
        cur.execute("INSERT OR REPLACE INTO comments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
            c.get("comment_id"),
            c.get("video_id"),
            c.get("parent_id"),
            c.get("author_display_name"),
            c.get("text_original"),
            c.get("text_clean"),
            c.get("like_count"),
            c.get("total_reply_count"),
            c.get("published_at"),
            c.get("updated_at"),
            c.get("comment_type"),
            1 if c.get("is_public", True) else 0,
        ))
    conn.commit()


def insert_transcripts(conn, transcripts):
    cur = conn.cursor()
    for t in transcripts:
        vid = t.get("video_id")
        cur.execute("INSERT OR REPLACE INTO transcripts VALUES (?,?,?,?,?)", (
            vid,
            t.get("status"),
            t.get("segment_count"),
            t.get("text_original"),
            t.get("text_clean"),
        ))
        for lang in (t.get("language_attempted") or []):
            cur.execute("INSERT INTO transcript_languages (video_id, language) VALUES (?,?)",
                        (vid, lang))
        for s in (t.get("segments") or []):
            cur.execute(
                "INSERT INTO transcript_segments (video_id, text, start, duration) VALUES (?,?,?,?)",
                (vid, s.get("text"), s.get("start"), s.get("duration")))
    conn.commit()


def insert_keywords(conn, keyword_data):
    cur = conn.cursor()
    for k in keyword_data:
        rid = cur.execute(
            "INSERT INTO keyword_results (video_id, text_length, keyword_count) VALUES (?,?,?)",
            (k.get("video_id"), k.get("text_length"), k.get("keyword_count"))).lastrowid
        for item in (k.get("keywords") or []):
            cur.execute(
                "INSERT INTO keyword_items (keyword_result_id, keyword, score) VALUES (?,?,?)",
                (rid, item.get("keyword"), item.get("score")))
    conn.commit()


def insert_ner(conn, ner_data):
    cur = conn.cursor()
    for n in ner_data:
        rid = cur.execute(
            """INSERT INTO ner_results
               (source_type, video_id, document_id, text_clean, entity_count)
               VALUES (?,?,?,?,?)""",
            (n.get("source_type"), n.get("video_id"), n.get("document_id"),
             n.get("text_clean"), n.get("entity_count"))).lastrowid
        for e in (n.get("entities") or []):
            cur.execute("INSERT INTO ner_entities (ner_result_id, text, label) VALUES (?,?,?)",
                        (rid, e.get("text"), e.get("label")))
    conn.commit()


def insert_topics(conn, topic_data):
    cur = conn.cursor()
    for t in topic_data:
        cur.execute(
            "INSERT INTO topic_results (video_id, text, topic, probability) VALUES (?,?,?,?)",
            (t.get("video_id"), t.get("text"), t.get("topic"), t.get("probability")))
    conn.commit()


def insert_topic_by_sentiment(conn, data):
    cur = conn.cursor()
    for grp in data:
        hid = cur.execute(
            """INSERT INTO topic_by_sentiment_results
               (sentiment_label, document_count, topic_count) VALUES (?,?,?)""",
            (grp.get("sentiment_label"), grp.get("document_count"),
             grp.get("topic_count"))).lastrowid
        for t in (grp.get("topics") or []):
            tid = cur.execute(
                """INSERT INTO tbs_topics
                   (topic_by_sentiment_id, sentiment_label, topic, count) VALUES (?,?,?,?)""",
                (hid, t.get("sentiment_label"), t.get("topic"), t.get("count"))).lastrowid
            for w in (t.get("topic_words") or []):
                cur.execute(
                    "INSERT INTO tbs_topic_words (tbs_topic_id, word, score) VALUES (?,?,?)",
                    (tid, w.get("word"), w.get("score")))
            for c in (t.get("representative_comments") or []):
                cur.execute(
                    """INSERT INTO tbs_representative_comments
                       (tbs_topic_id, comment_id, video_id, text, compound, like_count)
                       VALUES (?,?,?,?,?,?)""",
                    (tid, c.get("comment_id"), c.get("video_id"), c.get("text"),
                     c.get("compound"), c.get("like_count")))
    conn.commit()


def insert_sentiment(conn, sentiment_data):
    cur = conn.cursor()
    for s in sentiment_data:
        cur.execute(
            """INSERT INTO sentiment_results
               (video_id, comment_id, parent_id, text_clean, negative, neutral, positive,
                compound, sentiment_label, like_count, published_at, comment_type)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s.get("video_id"), s.get("comment_id"), s.get("parent_id"), s.get("text_clean"),
             s.get("negative"), s.get("neutral"), s.get("positive"), s.get("compound"),
             s.get("sentiment_label"), s.get("like_count"), s.get("published_at"),
             s.get("comment_type")))
    conn.commit()


def insert_youtube_relations(conn, relation_data):
    cur = conn.cursor()
    for r in relation_data:
        if not row_exists(conn, "videos", "video_id", r.get("video_id")):
            continue
        rid = cur.execute(
            """INSERT INTO youtube_relation_results
               (source_type, video_id, document_id, text_clean, relation_count)
               VALUES (?,?,?,?,?)""",
            (r.get("source_type"), r.get("video_id"), r.get("document_id"),
             r.get("text_clean"), r.get("relation_count"))).lastrowid
        for rel in (r.get("relations") or []):
            cur.execute(
                """INSERT INTO youtube_relations
                   (relation_result_id, subject_text, relation, object_text,
                    relation_text, confidence, matched_rule)
                   VALUES (?,?,?,?,?,?,?)""",
                (rid, rel.get("subject"), rel.get("relation"), rel.get("object"),
                 rel.get("relation_text"), rel.get("confidence"), rel.get("matched_rule")))
    conn.commit()


# ============================================================================
# HACKERNEWS
# ============================================================================
def insert_hackernews(conn, records):
    cur = conn.cursor()
    for r in records:
        cur.execute("INSERT OR REPLACE INTO hackernews VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            r.get("record_id"),
            r.get("source"),
            r.get("story_id"),
            r.get("parent_id"),
            r.get("author"),
            r.get("title"),
            r.get("url"),
            r.get("text_original"),
            r.get("text_clean"),
            r.get("points"),
            r.get("num_comments"),
            r.get("created_at"),
            r.get("query"),
        ))
    conn.commit()


def insert_hn_keywords(conn, data):
    cur = conn.cursor()
    for k in data:
        rid = cur.execute(
            """INSERT INTO hackernews_keyword_results
               (record_id, story_id, author, text_length, keyword_count) VALUES (?,?,?,?,?)""",
            (k.get("record_id"), k.get("story_id"), k.get("author"),
             k.get("text_length"), k.get("keyword_count"))).lastrowid
        for item in (k.get("keywords") or []):
            cur.execute(
                """INSERT INTO hackernews_keyword_items
                   (hn_keyword_result_id, keyword, score) VALUES (?,?,?)""",
                (rid, item.get("keyword"), item.get("score")))
    conn.commit()


def insert_hn_ner(conn, data):
    cur = conn.cursor()
    for n in data:
        rid = cur.execute(
            """INSERT INTO hackernews_ner_results
               (record_id, story_id, author, entity_count) VALUES (?,?,?,?)""",
            (n.get("record_id"), n.get("story_id"), n.get("author"),
             n.get("entity_count"))).lastrowid
        for e in (n.get("entities") or []):
            cur.execute(
                "INSERT INTO hackernews_ner_entities (hn_ner_result_id, text, label) VALUES (?,?,?)",
                (rid, e.get("text"), e.get("label")))
    conn.commit()


def insert_hn_topics(conn, data):
    cur = conn.cursor()
    for t in data:
        cur.execute(
            """INSERT INTO hackernews_topic_results
               (record_id, story_id, text, topic, probability) VALUES (?,?,?,?,?)""",
            (t.get("record_id"), t.get("story_id"), t.get("text"),
             t.get("topic"), t.get("probability")))
    conn.commit()


def insert_hn_sentiment(conn, data):
    cur = conn.cursor()
    for s in data:
        cur.execute(
            """INSERT INTO hackernews_sentiment_results
               (record_id, story_id, author, text_length, negative, neutral, positive,
                compound, sentiment_label, points, num_comments, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s.get("record_id"), s.get("story_id"), s.get("author"), s.get("text_length"),
             s.get("negative"), s.get("neutral"), s.get("positive"), s.get("compound"),
             s.get("sentiment_label"), s.get("points"), s.get("num_comments"),
             s.get("created_at")))
    conn.commit()


def insert_hn_relations(conn, data):
    cur = conn.cursor()
    for r in data:
        if not row_exists(conn, "hackernews", "record_id", r.get("record_id")):
            continue
        rid = cur.execute(
            """INSERT INTO hackernews_relation_results
               (source, record_id, story_id, author, text_clean, relation_count)
               VALUES (?,?,?,?,?,?)""",
            (r.get("source"), r.get("record_id"), r.get("story_id"), r.get("author"),
             r.get("text_clean"), r.get("relation_count"))).lastrowid
        for rel in (r.get("relations") or []):
            cur.execute(
                """INSERT INTO hackernews_relations
                   (relation_result_id, subject_text, relation, object_text,
                    relation_text, confidence, matched_rule)
                   VALUES (?,?,?,?,?,?,?)""",
                (rid, rel.get("subject"), rel.get("relation"), rel.get("object"),
                 rel.get("relation_text"), rel.get("confidence"), rel.get("matched_rule")))
    conn.commit()


def insert_hn_topic_by_sentiment(conn, data):
    cur = conn.cursor()
    for grp in data:
        hid = cur.execute(
            """INSERT INTO hackernews_topic_by_sentiment_results
               (sentiment_label, document_count, topic_count) VALUES (?,?,?)""",
            (grp.get("sentiment_label"), grp.get("document_count"),
             grp.get("topic_count"))).lastrowid
        for t in (grp.get("topics") or []):
            tid = cur.execute(
                """INSERT INTO hn_tbs_topics
                   (hn_topic_by_sentiment_id, sentiment_label, topic, count) VALUES (?,?,?,?)""",
                (hid, t.get("sentiment_label"), t.get("topic"), t.get("count"))).lastrowid
            for w in (t.get("topic_words") or []):
                cur.execute(
                    "INSERT INTO hn_tbs_topic_words (hn_tbs_topic_id, word, score) VALUES (?,?,?)",
                    (tid, w.get("word"), w.get("score")))
            for p in (t.get("representative_posts") or []):
                cur.execute(
                    """INSERT INTO hn_tbs_representative_posts
                       (hn_tbs_topic_id, record_id, story_id, text, compound, score)
                       VALUES (?,?,?,?,?,?)""",
                    (tid, p.get("record_id"), p.get("story_id"), p.get("text"),
                     p.get("compound"), p.get("score")))
    conn.commit()


# ============================================================================
# RESEARCH
# ============================================================================
def insert_research_sources(conn, records):
    cur = conn.cursor()
    for r in records:
        rid = r.get("record_id")
        cur.execute("INSERT OR REPLACE INTO research_sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            rid,
            r.get("source"),
            r.get("query"),
            r.get("doi"),
            r.get("title"),
            r.get("title_clean"),
            r.get("abstract"),
            r.get("text_original"),
            r.get("text_clean"),
            r.get("text_for_rag"),
            r.get("published_at"),
            r.get("updated_at"),
            r.get("url"),
            r.get("venue"),
        ))
        for i, author in enumerate(r.get("authors") or []):
            cur.execute(
                "INSERT INTO research_authors (record_id, author_name, author_order) VALUES (?,?,?)",
                (rid, author, i))
    conn.commit()


def insert_research_keywords(conn, data):
    cur = conn.cursor()
    for k in data:
        rid = cur.execute(
            """INSERT INTO research_keyword_results
               (record_id, doi, title, keyword_count) VALUES (?,?,?,?)""",
            (k.get("record_id"), k.get("doi"), k.get("title"),
             k.get("keyword_count"))).lastrowid
        for item in (k.get("keywords") or []):
            cur.execute(
                """INSERT INTO research_keyword_items
                   (research_keyword_result_id, keyword, score) VALUES (?,?,?)""",
                (rid, item.get("keyword"), item.get("score")))
    conn.commit()


def insert_research_ner(conn, data):
    cur = conn.cursor()
    for n in data:
        rid = cur.execute(
            """INSERT INTO research_ner_results
               (record_id, doi, title, entity_count) VALUES (?,?,?,?)""",
            (n.get("record_id"), n.get("doi"), n.get("title"),
             n.get("entity_count"))).lastrowid
        for e in (n.get("entities") or []):
            cur.execute(
                """INSERT INTO research_ner_entities
                   (research_ner_result_id, text, label) VALUES (?,?,?)""",
                (rid, e.get("text"), e.get("label")))
    conn.commit()


def insert_research_topics(conn, data):
    cur = conn.cursor()
    for t in data:
        cur.execute(
            """INSERT INTO research_topic_results
               (record_id, doi, title, topic, probability) VALUES (?,?,?,?,?)""",
            (t.get("record_id"), t.get("doi"), t.get("title"),
             t.get("topic"), t.get("probability")))
    conn.commit()


def insert_research_relations(conn, data):
    cur = conn.cursor()
    for r in data:
        if not row_exists(conn, "research_sources", "record_id", r.get("record_id")):
            continue
        rid = cur.execute(
            """INSERT INTO research_relation_results
               (source, record_id, doi, title, text_clean, relation_count)
               VALUES (?,?,?,?,?,?)""",
            (r.get("source"), r.get("record_id"), r.get("doi"), r.get("title"),
             r.get("text_clean"), r.get("relation_count"))).lastrowid
        for rel in (r.get("relations") or []):
            cur.execute(
                """INSERT INTO research_relations
                   (relation_result_id, subject_text, relation, object_text,
                    relation_text, confidence, matched_rule)
                   VALUES (?,?,?,?,?,?,?)""",
                (rid, rel.get("subject"), rel.get("relation"), rel.get("object"),
                 rel.get("relation_text"), rel.get("confidence"), rel.get("matched_rule")))
    conn.commit()


# ============================================================================
# MAIN PIPELINE
# ============================================================================
def main():
    conn = init_db()

    # ---- YouTube ----------------------------------------------------------
    print("YouTube:")
    insert_videos(conn, load_json(PREP / "clean_videos.json"))
    insert_transcripts(conn, load_json(PREP / "clean_transcripts.json"))
    insert_comments(conn, load_json(PREP / "clean_comments.json"))
    insert_keywords(conn, load_json(FEAT / "keyword_results.json"))
    insert_ner(conn, load_json(FEAT / "ner_results.json"))
    insert_topics(conn, load_json(FEAT / "topic_results.json"))
    insert_topic_by_sentiment(conn, load_json(FEAT / "topic_by_sentiment_results.json"))
    insert_sentiment(conn, load_json(FEAT / "sentiment_results.json"))
    insert_youtube_relations(conn, load_json(FEAT / "youtube_relation_results.json"))

    # ---- HackerNews -------------------------------------------------------
    print("HackerNews:")
    insert_hackernews(conn, load_json(PREP / "clean_hackernews.json"))
    insert_hn_keywords(conn, load_json(FEAT / "hackernews_keyword_results.json"))
    insert_hn_ner(conn, load_json(FEAT / "hackernews_ner_results.json"))
    insert_hn_topics(conn, load_json(FEAT / "hackernews_topic_results.json"))
    insert_hn_sentiment(conn, load_json(FEAT / "hackernews_sentiment_results.json"))
    insert_hn_relations(conn, load_json(FEAT / "hackernews_relation_results.json"))
    insert_hn_topic_by_sentiment(conn, load_json(FEAT / "hackernews_topic_by_sentiment_results.json"))

    # ---- Research ---------------------------------------------------------
    print("Research:")
    insert_research_sources(conn, load_json(PREP / "clean_research_sources.json"))
    insert_research_keywords(conn, load_json(FEAT / "research_keyword_results.json"))
    insert_research_ner(conn, load_json(FEAT / "research_ner_results.json"))
    insert_research_topics(conn, load_json(FEAT / "research_topic_results.json"))
    insert_research_relations(conn, load_json(FEAT / "research_relation_results.json"))

    problems = conn.execute("PRAGMA foreign_key_check").fetchall()
    print("\nForeign-key check:", problems if problems else "clean")
    conn.close()
    print("Structured database population complete.")


if __name__ == "__main__":
    main()
