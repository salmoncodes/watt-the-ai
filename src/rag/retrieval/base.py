"""Shared types for the RAG retrievers."""

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
    """Open a SQLite connection with row access by name."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


class Retriever(ABC):
    """Common retriever interface."""

    name = "base"

    @abstractmethod
    def retrieve(self, query, top_k=TOP_K, filters=None):
        raise NotImplementedError
