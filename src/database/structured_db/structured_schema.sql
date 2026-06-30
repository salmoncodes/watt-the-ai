-- structured_schema.sql
-- Structured Database Schema (Relational Layer)
-- Stores cleaned data + NLP feature outputs for analytics and filtering

PRAGMA foreign_keys = ON;


-- #############################################################################
-- # SOURCE 1: YOUTUBE
-- #############################################################################

-- Core YouTube video metadata (clean_videos.json). One row per video.
CREATE TABLE videos (
    video_id            TEXT PRIMARY KEY,          -- natural key
    title_original      TEXT,
    title_clean         TEXT,
    description_original TEXT,
    description_clean   TEXT,
    channel_id          TEXT,
    channel_title       TEXT,
    published_at        TEXT,                       -- ISO-8601 timestamp
    category_id         TEXT,
    duration            TEXT,                       -- ISO-8601 duration, e.g. PT24M
    caption             TEXT,                       -- literal "true"/"false" as in source
    view_count          INTEGER,
    like_count          INTEGER,
    comment_count       INTEGER
);

-- Tags attached to a video (videos.tags[] is a relational array of strings).
CREATE TABLE video_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id    TEXT NOT NULL,
    tag         TEXT,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);

-- YouTube comments (clean_comments.json). Many comments per video.
CREATE TABLE comments (
    comment_id          TEXT PRIMARY KEY,           -- natural key
    video_id            TEXT NOT NULL,
    parent_id           TEXT,
    author_display_name TEXT,
    text_original       TEXT,
    text_clean          TEXT,
    like_count          INTEGER,
    total_reply_count   INTEGER,
    published_at        TEXT,
    updated_at          TEXT,
    comment_type        TEXT,
    is_public           INTEGER,                    -- boolean stored as 0/1
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);

-- Transcript header (clean_transcripts.json). One-to-one with a video.
CREATE TABLE transcripts (
    video_id        TEXT PRIMARY KEY,               -- natural key (1:1 with videos)
    status          TEXT,
    segment_count   INTEGER,
    text_original   TEXT,
    text_clean      TEXT,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);

-- Languages attempted for a transcript (language_attempted[] relational array).
CREATE TABLE transcript_languages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id    TEXT NOT NULL,
    language    TEXT,
    FOREIGN KEY (video_id) REFERENCES transcripts (video_id)
);

-- Individual transcript segments (segments[] relational array of objects).
CREATE TABLE transcript_segments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id    TEXT NOT NULL,
    text        TEXT,
    start       REAL,
    duration    REAL,
    FOREIGN KEY (video_id) REFERENCES transcripts (video_id)
);


-- ----- YouTube NLP: KEYWORDS (keyword_results.json) -------------------------

-- Keyword-extraction header for a video. No natural key -> generated id.
CREATE TABLE keyword_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id        TEXT NOT NULL,
    text_length     INTEGER,
    keyword_count   INTEGER,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);

-- Individual extracted keywords (keywords[] relational array of objects).
CREATE TABLE keyword_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_result_id   INTEGER NOT NULL,
    keyword             TEXT,
    score               REAL,
    FOREIGN KEY (keyword_result_id) REFERENCES keyword_results (id)
);


-- ----- YouTube NLP: NER (ner_results.json) ----------------------------------

-- Named-entity-recognition header per document. No natural key -> generated id.
CREATE TABLE ner_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT,                           -- comment / transcript / video
    video_id        TEXT NOT NULL,
    document_id     TEXT,                           -- e.g. comment_id of the document
    text_clean      TEXT,
    entity_count    INTEGER,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);

-- Recognised entities (entities[] relational array of objects).
CREATE TABLE ner_entities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ner_result_id   INTEGER NOT NULL,
    text            TEXT,
    label           TEXT,
    FOREIGN KEY (ner_result_id) REFERENCES ner_results (id)
);


-- ----- YouTube NLP: TOPICS (topic_results.json) -----------------------------

-- Per-video topic assignment. No natural key -> generated id.
CREATE TABLE topic_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id        TEXT NOT NULL,
    text            TEXT,
    topic           INTEGER,
    probability     REAL,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);


-- ----- YouTube NLP: TOPIC-BY-SENTIMENT (topic_by_sentiment_results.json) -----

-- Aggregate header grouping topics under one sentiment label.
CREATE TABLE topic_by_sentiment_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sentiment_label TEXT,
    document_count  INTEGER,
    topic_count     INTEGER
);

-- A topic within a sentiment group (topics[] relational array of objects).
CREATE TABLE tbs_topics (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_by_sentiment_id   INTEGER NOT NULL,
    sentiment_label         TEXT,
    topic                   INTEGER,
    count                   INTEGER,
    FOREIGN KEY (topic_by_sentiment_id) REFERENCES topic_by_sentiment_results (id)
);

-- Top words for a topic (topic_words[] relational array of objects).
CREATE TABLE tbs_topic_words (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tbs_topic_id    INTEGER NOT NULL,
    word            TEXT,
    score           REAL,
    FOREIGN KEY (tbs_topic_id) REFERENCES tbs_topics (id)
);

-- Representative comments for a topic (representative_comments[] relational array).
-- comment_id / video_id are cross-references to the comments/videos tables;
-- kept as plain columns to avoid load-time referential-integrity failures.
CREATE TABLE tbs_representative_comments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tbs_topic_id    INTEGER NOT NULL,
    comment_id      TEXT,
    video_id        TEXT,
    text            TEXT,
    compound        REAL,
    like_count      INTEGER,
    FOREIGN KEY (tbs_topic_id) REFERENCES tbs_topics (id)
);


-- ----- YouTube NLP: SENTIMENT (sentiment_results.json) ----------------------

-- Per-comment sentiment scores. No natural key -> generated id.
CREATE TABLE sentiment_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id        TEXT NOT NULL,
    comment_id      TEXT,
    parent_id       TEXT,
    text_clean      TEXT,
    negative        REAL,
    neutral         REAL,
    positive        REAL,
    compound        REAL,
    sentiment_label TEXT,
    like_count      INTEGER,
    published_at    TEXT,
    comment_type    TEXT,
    FOREIGN KEY (video_id)   REFERENCES videos (video_id),
    FOREIGN KEY (comment_id) REFERENCES comments (comment_id)
);


-- ----- YouTube NLP: RELATIONS (youtube_relation_results.json) ----------------

-- Relation-extraction header per document. No natural key -> generated id.
CREATE TABLE youtube_relation_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT,
    video_id        TEXT NOT NULL,
    document_id     TEXT,
    text_clean      TEXT,
    relation_count  INTEGER,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);

CREATE TABLE youtube_relations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    relation_result_id  INTEGER NOT NULL,
    subject_text        TEXT,
    relation            TEXT,
    object_text         TEXT,
    relation_text       TEXT,   
    confidence          REAL,
    matched_rule        TEXT,   
    FOREIGN KEY (relation_result_id) REFERENCES youtube_relation_results (id)
);


-- #############################################################################
-- # SOURCE 2: HACKERNEWS  (independent source)
-- #############################################################################

-- Core HackerNews records (clean_hackernews.json). One row per record.
CREATE TABLE hackernews (
    record_id       TEXT PRIMARY KEY,               -- natural key
    source          TEXT,
    story_id        INTEGER,
    parent_id       INTEGER,
    author          TEXT,
    title           TEXT,
    url             TEXT,
    text_original   TEXT,
    text_clean      TEXT,
    points          INTEGER,                        -- nullable
    num_comments    INTEGER,                        -- nullable
    created_at      TEXT,
    query           TEXT
);


-- ----- HackerNews NLP: KEYWORDS (hackernews_keyword_results.json) ------------

CREATE TABLE hackernews_keyword_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    story_id        INTEGER,
    author          TEXT,
    text_length     INTEGER,
    keyword_count   INTEGER,
    FOREIGN KEY (record_id) REFERENCES hackernews (record_id)
);

-- Individual extracted keywords (keywords[] relational array of objects).
CREATE TABLE hackernews_keyword_items (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    hn_keyword_result_id    INTEGER NOT NULL,
    keyword                 TEXT,
    score                   REAL,
    FOREIGN KEY (hn_keyword_result_id) REFERENCES hackernews_keyword_results (id)
);


-- ----- HackerNews NLP: NER (hackernews_ner_results.json) ---------------------

CREATE TABLE hackernews_ner_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    story_id        INTEGER,
    author          TEXT,
    entity_count    INTEGER,
    FOREIGN KEY (record_id) REFERENCES hackernews (record_id)
);

-- Recognised entities (entities[] relational array of objects).
CREATE TABLE hackernews_ner_entities (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    hn_ner_result_id    INTEGER NOT NULL,
    text                TEXT,
    label               TEXT,
    FOREIGN KEY (hn_ner_result_id) REFERENCES hackernews_ner_results (id)
);


-- ----- HackerNews NLP: TOPICS (hackernews_topic_results.json) ----------------

CREATE TABLE hackernews_topic_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    story_id        INTEGER,
    text            TEXT,
    topic           INTEGER,
    probability     REAL,
    FOREIGN KEY (record_id) REFERENCES hackernews (record_id)
);


-- ----- HackerNews NLP: SENTIMENT (hackernews_sentiment_results.json) ---------

CREATE TABLE hackernews_sentiment_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    story_id        INTEGER,
    author          TEXT,
    text_length     INTEGER,
    negative        REAL,
    neutral         REAL,
    positive        REAL,
    compound        REAL,
    sentiment_label TEXT,
    points          INTEGER,                        -- nullable
    num_comments    INTEGER,                        -- nullable
    created_at      TEXT,
    FOREIGN KEY (record_id) REFERENCES hackernews (record_id)
);


-- ----- HackerNews NLP: RELATIONS (hackernews_relation_results.json) ----------

CREATE TABLE hackernews_relation_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT,
    record_id       TEXT NOT NULL,
    story_id        INTEGER,
    author          TEXT,
    text_clean      TEXT,
    relation_count  INTEGER,
    FOREIGN KEY (record_id) REFERENCES hackernews (record_id)
);


CREATE TABLE hackernews_relations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    relation_result_id  INTEGER NOT NULL,
    subject_text        TEXT,
    relation            TEXT,
    object_text         TEXT,
    relation_text       TEXT,   -- new: formatted "relation(subject, object)" string
    confidence          REAL,
    matched_rule        TEXT,   -- new: extraction rule that fired
    FOREIGN KEY (relation_result_id) REFERENCES hackernews_relation_results (id)
);


-- ----- HackerNews NLP: TOPIC-BY-SENTIMENT -----------------------------------
-- (hackernews_topic_by_sentiment_results.json)

CREATE TABLE hackernews_topic_by_sentiment_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sentiment_label TEXT,
    document_count  INTEGER,
    topic_count     INTEGER
);

-- A topic within a sentiment group (topics[] relational array of objects).
CREATE TABLE hn_tbs_topics (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    hn_topic_by_sentiment_id    INTEGER NOT NULL,
    sentiment_label             TEXT,
    topic                       INTEGER,
    count                       INTEGER,
    FOREIGN KEY (hn_topic_by_sentiment_id)
        REFERENCES hackernews_topic_by_sentiment_results (id)
);

-- Top words for a topic (topic_words[] relational array of objects).
CREATE TABLE hn_tbs_topic_words (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    hn_tbs_topic_id     INTEGER NOT NULL,
    word                TEXT,
    score               REAL,
    FOREIGN KEY (hn_tbs_topic_id) REFERENCES hn_tbs_topics (id)
);

-- Representative posts for a topic (representative_posts[] relational array).
-- record_id / story_id are cross-references kept as plain columns.
CREATE TABLE hn_tbs_representative_posts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    hn_tbs_topic_id     INTEGER NOT NULL,
    record_id           TEXT,
    story_id            TEXT,
    text                TEXT,
    compound            REAL,
    score               REAL,
    FOREIGN KEY (hn_tbs_topic_id) REFERENCES hn_tbs_topics (id)
);


-- #############################################################################
-- # SOURCE 3: RESEARCH  (independent source)
-- #############################################################################

-- Core research source records (clean_research_sources.json). One row per record.
CREATE TABLE research_sources (
    record_id       TEXT PRIMARY KEY,               -- natural key (e.g. OpenAlex URL)
    source          TEXT,
    query           TEXT,
    doi             TEXT,
    title           TEXT,
    title_clean     TEXT,
    abstract        TEXT,
    text_original   TEXT,
    text_clean      TEXT,
    text_for_rag    TEXT,
    published_at    TEXT,
    updated_at      TEXT,
    url             TEXT,
    venue           TEXT
);

-- Authors of a research source (authors[] relational array of strings).
-- author_order preserves the original ordering of the array.
CREATE TABLE research_authors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    author_name     TEXT,
    author_order    INTEGER,
    FOREIGN KEY (record_id) REFERENCES research_sources (record_id)
);


-- ----- Research NLP: KEYWORDS (research_keyword_results.json) ----------------

CREATE TABLE research_keyword_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    doi             TEXT,
    title           TEXT,
    keyword_count   INTEGER,
    FOREIGN KEY (record_id) REFERENCES research_sources (record_id)
);

-- Individual extracted keywords (keywords[] relational array of objects).
CREATE TABLE research_keyword_items (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    research_keyword_result_id  INTEGER NOT NULL,
    keyword                     TEXT,
    score                       REAL,
    FOREIGN KEY (research_keyword_result_id)
        REFERENCES research_keyword_results (id)
);


-- ----- Research NLP: NER (research_ner_results.json) -------------------------

CREATE TABLE research_ner_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    doi             TEXT,
    title           TEXT,
    entity_count    INTEGER,
    FOREIGN KEY (record_id) REFERENCES research_sources (record_id)
);

-- Recognised entities (entities[] relational array of objects).
CREATE TABLE research_ner_entities (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    research_ner_result_id  INTEGER NOT NULL,
    text                    TEXT,
    label                   TEXT,
    FOREIGN KEY (research_ner_result_id) REFERENCES research_ner_results (id)
);


-- ----- Research NLP: TOPICS (research_topic_results.json) --------------------

CREATE TABLE research_topic_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL,
    doi             TEXT,
    title           TEXT,
    topic           INTEGER,
    probability     REAL,
    FOREIGN KEY (record_id) REFERENCES research_sources (record_id)
);


-- ----- Research NLP: RELATIONS (research_relation_results.json) --------------

CREATE TABLE research_relation_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT,
    record_id       TEXT NOT NULL,
    doi             TEXT,
    title           TEXT,
    text_clean      TEXT,
    relation_count  INTEGER,
    FOREIGN KEY (record_id) REFERENCES research_sources (record_id)
);

CREATE TABLE research_relations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    relation_result_id  INTEGER NOT NULL,
    subject_text        TEXT,
    relation            TEXT,
    object_text         TEXT,
    relation_text       TEXT,  
    confidence          REAL,
    matched_rule        TEXT,   
    FOREIGN KEY (relation_result_id) REFERENCES research_relation_results (id)
);


-- #############################################################################
-- # INDEXES on foreign-key columns (query performance)
-- #############################################################################
CREATE INDEX idx_video_tags_video              ON video_tags (video_id);
CREATE INDEX idx_comments_video                ON comments (video_id);
CREATE INDEX idx_transcript_langs_video        ON transcript_languages (video_id);
CREATE INDEX idx_transcript_segs_video         ON transcript_segments (video_id);
CREATE INDEX idx_keyword_results_video         ON keyword_results (video_id);
CREATE INDEX idx_keyword_items_parent          ON keyword_items (keyword_result_id);
CREATE INDEX idx_ner_results_video             ON ner_results (video_id);
CREATE INDEX idx_ner_entities_parent           ON ner_entities (ner_result_id);
CREATE INDEX idx_topic_results_video           ON topic_results (video_id);
CREATE INDEX idx_tbs_topics_parent             ON tbs_topics (topic_by_sentiment_id);
CREATE INDEX idx_tbs_words_parent              ON tbs_topic_words (tbs_topic_id);
CREATE INDEX idx_tbs_repcomments_parent        ON tbs_representative_comments (tbs_topic_id);
CREATE INDEX idx_sentiment_results_video       ON sentiment_results (video_id);
CREATE INDEX idx_sentiment_results_comment     ON sentiment_results (comment_id);
CREATE INDEX idx_yt_rel_results_video          ON youtube_relation_results (video_id);
CREATE INDEX idx_yt_relations_parent           ON youtube_relations (relation_result_id);

CREATE INDEX idx_hn_kw_results_record          ON hackernews_keyword_results (record_id);
CREATE INDEX idx_hn_kw_items_parent            ON hackernews_keyword_items (hn_keyword_result_id);
CREATE INDEX idx_hn_ner_results_record         ON hackernews_ner_results (record_id);
CREATE INDEX idx_hn_ner_entities_parent        ON hackernews_ner_entities (hn_ner_result_id);
CREATE INDEX idx_hn_topic_results_record       ON hackernews_topic_results (record_id);
CREATE INDEX idx_hn_sent_results_record        ON hackernews_sentiment_results (record_id);
CREATE INDEX idx_hn_rel_results_record         ON hackernews_relation_results (record_id);
CREATE INDEX idx_hn_relations_parent           ON hackernews_relations (relation_result_id);
CREATE INDEX idx_hn_tbs_topics_parent          ON hn_tbs_topics (hn_topic_by_sentiment_id);
CREATE INDEX idx_hn_tbs_words_parent           ON hn_tbs_topic_words (hn_tbs_topic_id);
CREATE INDEX idx_hn_tbs_repposts_parent        ON hn_tbs_representative_posts (hn_tbs_topic_id);

CREATE INDEX idx_research_authors_record       ON research_authors (record_id);
CREATE INDEX idx_research_kw_results_record    ON research_keyword_results (record_id);
CREATE INDEX idx_research_kw_items_parent      ON research_keyword_items (research_keyword_result_id);
CREATE INDEX idx_research_ner_results_record   ON research_ner_results (record_id);
CREATE INDEX idx_research_ner_entities_parent  ON research_ner_entities (research_ner_result_id);
CREATE INDEX idx_research_topic_results_record ON research_topic_results (record_id);
CREATE INDEX idx_research_rel_results_record   ON research_relation_results (record_id);
CREATE INDEX idx_research_relations_parent     ON research_relations (relation_result_id);
