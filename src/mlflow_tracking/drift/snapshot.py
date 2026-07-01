"""
snapshot.py

Collects a point-in-time "snapshot" of the project's databases: table row
counts, sentiment distribution, topic distribution, and keyword
distribution (real table or a stdlib word-frequency fallback).

Retrieval behavior is intentionally NOT collected here -- see
retrieval_check.py.
"""

import sqlite3
from collections import Counter
from pathlib import Path

from mlflow_tracking.tracking import STRUCTURED_DB_PATH, VECTOR_DB_PATH
from mlflow_tracking.drift.config import (
    SENTIMENT_PREFERRED_TABLES,
    SENTIMENT_COLUMN_CANDIDATES,
    TOPIC_NAME_SUBSTRINGS,
    TOPIC_NAME_EXCLUDE_SUBSTRINGS,
    TOPIC_COLUMN_CANDIDATES,
    TOP_TOPIC_LIMIT,
    KEYWORD_NAME_SUBSTRINGS,
    KEYWORD_COLUMN_CANDIDATES,
    TOP_KEYWORD_LIMIT,
    FALLBACK_TEXT_TABLES,
    FALLBACK_TEXT_COLUMN_CANDIDATES,
    FALLBACK_TEXT_ROW_LIMIT,
    STOPWORDS,
    PUNCTUATION_TABLE,
)
from mlflow_tracking.drift.metrics import now_iso, normalize_distribution
from mlflow_tracking.drift.sqlite_utils import (
    connect_sqlite,
    list_tables,
    list_columns,
    get_table_counts,
    find_first_existing_column,
    get_distribution_from_table,
)
from mlflow_tracking.drift.retrieval_check import collect_retrieval_snapshot


def _describe_db_for_snapshot(db_path):
    info = {"path": str(db_path), "exists": Path(db_path).exists(), "tables": {}}
    if not info["exists"]:
        info["reason"] = "database file not found"
        return info
    info["tables"] = get_table_counts(db_path)
    return info


def collect_database_snapshot():
    """Row counts for every table in structured.db and vector.db."""
    return {
        "structured": _describe_db_for_snapshot(STRUCTURED_DB_PATH),
        "vector": _describe_db_for_snapshot(VECTOR_DB_PATH),
    }


def collect_sentiment_snapshot():
    """Sentiment label distribution from the structured DB, if available."""
    result = {
        "available": False,
        "reason": None,
        "source_table": None,
        "source_column": None,
        "counts": {},
        "distribution": {},
    }
    if not STRUCTURED_DB_PATH.exists():
        result["reason"] = "structured.db not found"
        return result

    tables = list_tables(STRUCTURED_DB_PATH)
    candidate_tables = [t for t in SENTIMENT_PREFERRED_TABLES if t in tables]
    candidate_tables += [
        t for t in tables if "sentiment" in t.lower() and t not in candidate_tables
    ]

    for table in candidate_tables:
        column = find_first_existing_column(
            list_columns(STRUCTURED_DB_PATH, table), SENTIMENT_COLUMN_CANDIDATES
        )
        if not column:
            continue
        counter = get_distribution_from_table(STRUCTURED_DB_PATH, table, column)
        if not counter:
            continue
        result.update({
            "available": True,
            "source_table": table,
            "source_column": column,
            "counts": dict(counter),
            "distribution": normalize_distribution(counter),
        })
        return result

    result["reason"] = "no sentiment table/column found"
    return result


def collect_topic_snapshot():
    """Topic distribution (top 20) from the structured DB, if a topic table exists."""
    result = {
        "available": False,
        "reason": None,
        "source_table": None,
        "source_column": None,
        "counts": {},
        "distribution": {},
    }
    if not STRUCTURED_DB_PATH.exists():
        result["reason"] = "structured.db not found"
        return result

    for table in list_tables(STRUCTURED_DB_PATH):
        name_lower = table.lower()
        if not any(sub in name_lower for sub in TOPIC_NAME_SUBSTRINGS):
            continue
        if any(sub in name_lower for sub in TOPIC_NAME_EXCLUDE_SUBSTRINGS):
            continue
        column = find_first_existing_column(
            list_columns(STRUCTURED_DB_PATH, table), TOPIC_COLUMN_CANDIDATES
        )
        if not column:
            continue
        counter = get_distribution_from_table(STRUCTURED_DB_PATH, table, column)
        if not counter:
            continue
        top_counts = dict(counter.most_common(TOP_TOPIC_LIMIT))
        result.update({
            "available": True,
            "source_table": table,
            "source_column": column,
            "counts": top_counts,
            "distribution": normalize_distribution(top_counts),
        })
        return result

    result["reason"] = "no topic table/column found"
    return result


def _tokenize_text(text):
    if not text:
        return []
    cleaned = str(text).lower().translate(PUNCTUATION_TABLE)
    return [w for w in cleaned.split() if len(w) >= 3 and w not in STOPWORDS]


def _collect_fallback_keyword_snapshot():
    """Simple word-frequency fallback over a few known text columns (stdlib only)."""
    counter = Counter()
    used_sources = []
    available_tables = set(list_tables(STRUCTURED_DB_PATH))

    for table in FALLBACK_TEXT_TABLES:
        if table not in available_tables:
            continue
        column = find_first_existing_column(
            list_columns(STRUCTURED_DB_PATH, table), FALLBACK_TEXT_COLUMN_CANDIDATES
        )
        if not column:
            continue
        conn = connect_sqlite(STRUCTURED_DB_PATH)
        if conn is None:
            continue
        try:
            query = (
                f'SELECT "{column}" FROM "{table}" '
                f'WHERE "{column}" IS NOT NULL LIMIT {FALLBACK_TEXT_ROW_LIMIT}'
            )
            for (text,) in conn.execute(query):
                counter.update(_tokenize_text(text))
            used_sources.append(f"{table}.{column}")
        except sqlite3.Error:
            continue
        finally:
            conn.close()

    if not counter:
        return None

    top_terms = dict(counter.most_common(TOP_KEYWORD_LIMIT))
    return {
        "available": True,
        "reason": None,
        "source": "fallback_text_frequency",
        "source_table": ", ".join(used_sources) if used_sources else None,
        "source_column": None,
        "top_terms": top_terms,
        "distribution": normalize_distribution(top_terms),
    }


def collect_keyword_snapshot():
    """Top-50 keyword distribution: a real keyword table if one exists, else a
    stdlib word-frequency fallback over comments/hackernews/research text."""
    result = {
        "available": False,
        "reason": None,
        "source": None,
        "source_table": None,
        "source_column": None,
        "top_terms": {},
        "distribution": {},
    }
    if not STRUCTURED_DB_PATH.exists():
        result["reason"] = "structured.db not found"
        return result

    for table in list_tables(STRUCTURED_DB_PATH):
        name_lower = table.lower()
        if not any(sub in name_lower for sub in KEYWORD_NAME_SUBSTRINGS):
            continue
        column = find_first_existing_column(
            list_columns(STRUCTURED_DB_PATH, table), KEYWORD_COLUMN_CANDIDATES
        )
        if not column:
            continue
        counter = get_distribution_from_table(STRUCTURED_DB_PATH, table, column)
        if not counter:
            continue
        top_terms = dict(counter.most_common(TOP_KEYWORD_LIMIT))
        result.update({
            "available": True,
            "source": "keyword_table",
            "source_table": table,
            "source_column": column,
            "top_terms": top_terms,
            "distribution": normalize_distribution(top_terms),
        })
        return result

    fallback = _collect_fallback_keyword_snapshot()
    if fallback is not None:
        return fallback

    result["reason"] = "no keyword table found and fallback text extraction found no text"
    return result


def _collect_snapshot(snapshot_type):
    return {
        "snapshot_type": snapshot_type,
        "created_at": now_iso(),
        "project": "watt-the-ai",
        "databases": collect_database_snapshot(),
        "sentiment": collect_sentiment_snapshot(),
        "topics": collect_topic_snapshot(),
        "keywords": collect_keyword_snapshot(),
        "retrieval": collect_retrieval_snapshot(),
    }


def collect_current_snapshot():
    """Collect a full "current" snapshot (databases + sentiment + topics + keywords + retrieval)."""
    return _collect_snapshot("current")
