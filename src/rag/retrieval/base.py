"""
base.py
Shared types for the retrieval strategies. Every strategy returns a list of
RetrievedDocument and implements the same retrieve() signature, so the agent
layer can treat them interchangeably and select one by name.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from rag.config.rag_config import TOP_K


@dataclass
class RetrievedDocument:
    document_id: str
    text: str
    score: float
    source: str                       # youtube | hackernews | research
    strategy: str                     # semantic | lexical | metadata | hybrid
    doc_type: Optional[str] = None
    metadata: dict = field(default_factory=dict)


def parse_metadata(raw):
    """Vector/structured metadata is stored as a JSON string; parse it safely."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}


def connect(db_path):
    """Open a read-only-style connection with row access by name."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


class Retriever(ABC):
    """Common interface. `query` is the user text, `filters` is an optional dict
    of structured constraints (e.g. {"source": "youtube", "sentiment": "negative"})."""

    name = "base"

    @abstractmethod
    def retrieve(self, query, top_k=TOP_K, filters=None):
        ...
