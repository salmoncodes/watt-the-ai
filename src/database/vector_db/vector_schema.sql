-- vector_schema.sql
-- Vector Database Schema (Semantic Retrieval Layer for RAG Foundation)
-- Stores unified documents (comments, transcript chunks, video summaries)
-- Designed for embedding-based similarity search

------------------------------------------------------------
-- YOUTUBE DOCUMENTS (comments, transcript chunks, video summaries)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS youtube_documents (
    document_id TEXT PRIMARY KEY,
    video_id    TEXT NOT NULL,      -- links to structured_db videos.video_id
    doc_type    TEXT NOT NULL,      -- comment | transcript_chunk | video_summary
    text        TEXT NOT NULL,      -- raw text used for embedding
    metadata    TEXT,               -- JSON string for flexible attributes
    embedding   TEXT                -- vector embedding (stored as text)
);

CREATE INDEX IF NOT EXISTS idx_yt_video_id ON youtube_documents(video_id);
CREATE INDEX IF NOT EXISTS idx_yt_doc_type ON youtube_documents(doc_type);


------------------------------------------------------------
-- HACKERNEWS DOCUMENTS (stories, comments, thread summaries)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hackernews_documents (
    document_id TEXT PRIMARY KEY,
    record_id   TEXT NOT NULL,      -- links to structured_db hackernews.record_id
    story_id    INTEGER,            -- thread grouping key (nullable, for filtering)
    doc_type    TEXT NOT NULL,      -- post | comment | story_summary | text_chunk
    text        TEXT NOT NULL,      -- raw text used for embedding
    metadata    TEXT,               -- JSON string for flexible attributes
    embedding   TEXT                -- vector embedding (stored as text)
);

CREATE INDEX IF NOT EXISTS idx_hn_record_id ON hackernews_documents(record_id);
CREATE INDEX IF NOT EXISTS idx_hn_story_id  ON hackernews_documents(story_id);
CREATE INDEX IF NOT EXISTS idx_hn_doc_type  ON hackernews_documents(doc_type);


------------------------------------------------------------
-- RESEARCH DOCUMENTS (abstract chunks, paper summaries)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_documents (
    document_id TEXT PRIMARY KEY,
    record_id   TEXT NOT NULL,      -- links to structured_db research_sources.record_id
    doi         TEXT,               -- digital object identifier (nullable, for filtering)
    doc_type    TEXT NOT NULL,      -- abstract_chunk | paper_summary | text_chunk
    text        TEXT NOT NULL,      -- raw text used for embedding
    metadata    TEXT,               -- JSON string for flexible attributes
    embedding   TEXT                -- vector embedding (stored as text)
);

CREATE INDEX IF NOT EXISTS idx_rs_record_id ON research_documents(record_id);
CREATE INDEX IF NOT EXISTS idx_rs_doi       ON research_documents(doi);
CREATE INDEX IF NOT EXISTS idx_rs_doc_type  ON research_documents(doc_type);
