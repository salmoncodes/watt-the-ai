-- vector_schema.sql
-- Vector Database Schema (Semantic Retrieval Layer for RAG Foundation)
-- Stores unified documents (comments, transcript chunks, video summaries)
-- Designed for embedding-based similarity search

PRAGMA foreign_keys = ON;

------------------------------------------------------------
-- DOCUMENTS TABLE (CORE VECTOR STORE)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,        -- comment | transcript_chunk | video_summary

    text TEXT NOT NULL,            -- raw text used for embedding

    metadata TEXT,                 -- JSON string for flexible attributes

    embedding BLOB                 -- vector embedding (stored as binary or serialized list)
);

------------------------------------------------------------
-- INDEXES FOR FILTERING (IMPORTANT FOR HYBRID SEARCH)
------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_video_id ON documents(video_id);
CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type);
