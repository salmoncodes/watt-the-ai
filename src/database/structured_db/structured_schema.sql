-- structured_schema.sql
-- Structured Database Schema (Relational Layer)
-- Stores cleaned data + NLP feature outputs for analytics and filtering

PRAGMA foreign_keys = ON;

------------------------------------------------------------
-- 1. VIDEOS TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    channel_id TEXT,
    channel_title TEXT,
    published_at TEXT,
    tags TEXT,              -- stored as JSON string
    category_id TEXT,
    duration TEXT,
    caption TEXT,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER
);

------------------------------------------------------------
-- 2. COMMENTS TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
    comment_id TEXT PRIMARY KEY,
    video_id TEXT,
    parent_id TEXT,
    author_display_name TEXT,
    text_original TEXT,
    like_count INTEGER,
    published_at TEXT,
    updated_at TEXT,
    total_reply_count INTEGER,
    is_public INTEGER,
    comment_type TEXT,

    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

------------------------------------------------------------
-- 3. TRANSCRIPTS TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transcripts (
    transcript_id TEXT PRIMARY KEY,
    video_id TEXT,
    text TEXT,
    status TEXT,
    language_attempted TEXT,

    start_time REAL,
    duration REAL,

    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

------------------------------------------------------------
-- 4. SENTIMENT RESULTS TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    document_id TEXT,
    doc_type TEXT,
    negative REAL,
    neutral REAL,
    positive REAL,
    compound REAL,
    label TEXT
);

------------------------------------------------------------
-- 5. NAMED ENTITY RECOGNITION TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ner_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    document_id TEXT,
    entity TEXT,
    entity_label TEXT,
    doc_type TEXT
);

------------------------------------------------------------
-- 6. KEYWORD EXTRACTION TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS keyword_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    document_id TEXT,
    keyword TEXT,
    score REAL,
    doc_type TEXT
);

------------------------------------------------------------
-- 7. TOPIC MODELING TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS topic_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    document_id TEXT,
    topic_id INTEGER,
    topic_score REAL,
    doc_type TEXT
);

------------------------------------------------------------
-- 8. HACKERNEWS TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hackernews (
    record_id TEXT PRIMARY KEY,
    source TEXT
    story_id INTEGER,
    parent_id INTEGER,
    author TEXT,
    title TEXT,
    URL TEXT,
    text_original TEXT,
    text_clean TEXT,
    points INTEGER,
    num_comments INTEGER,
    created_at TEXT,
    query TEXT
    );

------------------------------------------------------------
-- 9. HACKERNEWS SENTIMENT TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hackernews_sentiment_results (
    record_id TEXT,
    story_id INTEGER,
    author TEXT,
    text_length INTEGER,
    negative REAL,
    neutral REAL,
    positive REAL,
    compound REAL,
    sentiment_label TEXT,
    points INTEGER,
    num_comments INTEGER,
    created_at TEXT
    );

------------------------------------------------------------
-- 10. HACKERNEWS NER TABLE
------------------------------------------------------------
