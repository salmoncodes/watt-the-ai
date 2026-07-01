"""
sqlite_utils.py

Schema-aware, defensive SQLite helpers used by the drift package. Every
function here is safe to call against a missing file, a broken database,
or a table/column that doesn't exist -- they return empty/None values
instead of raising.

No MLflow, no drift comparison logic -- just database introspection.
"""

import sqlite3
from collections import Counter
from pathlib import Path


def connect_sqlite(db_path):
    """Open a read-only sqlite3 connection, or None if the file is missing/broken."""
    db_path = Path(db_path)
    if not db_path.exists():
        return None
    try:
        return sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None


def list_tables(db_path):
    """Return user table names found in `db_path` (excludes sqlite_* internals)."""
    conn = connect_sqlite(db_path)
    if conn is None:
        return []
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cur.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def list_columns(db_path, table):
    """Return column names for `table`, or [] if the table/db is unavailable."""
    conn = connect_sqlite(db_path)
    if conn is None:
        return []
    try:
        cur = conn.execute(f"PRAGMA table_info('{table}')")
        return [row[1] for row in cur.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_table_counts(db_path):
    """Return {table_name: row_count} for every table found in `db_path`."""
    conn = connect_sqlite(db_path)
    if conn is None:
        return {}
    counts = {}
    try:
        for table in list_tables(db_path):
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM '{table}'").fetchone()
                counts[table] = row[0] if row else 0
            except sqlite3.Error:
                counts[table] = None
    finally:
        conn.close()
    return counts


def find_first_existing_column(columns, candidates):
    """Return the first name in `candidates` that appears in `columns`, else None."""
    column_set = set(columns or [])
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def get_distribution_from_table(db_path, table, column, limit=None):
    """Return a Counter of value -> row count for `column` in `table`.

    Returns None (not {}) if the table/column can't be read at all, so
    callers can distinguish "no data" from "query failed".
    """
    conn = connect_sqlite(db_path)
    if conn is None:
        return None
    try:
        query = f'SELECT "{column}" FROM "{table}"'
        if limit:
            query += f" LIMIT {int(limit)}"
        counter = Counter()
        for (value,) in conn.execute(query):
            if value is None:
                continue
            counter[str(value).strip()] += 1
        return counter
    except sqlite3.Error:
        return None
    finally:
        conn.close()
