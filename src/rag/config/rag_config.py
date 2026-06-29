"""
rag_config.py
Central configuration for the RAG layer: database locations, the embedding
model, the vector tables to search, and retrieval defaults.

Nothing else in the layer hardcodes a path or model name; they all read from
here. EMBEDDING_MODEL in particular MUST match the model used in
transfer_to_vector.py, or query and document vectors will not be comparable.
"""

from pathlib import Path

# repo root:  src/rag/config/rag_config.py  ->  parents[3]
ROOT = Path(__file__).resolve().parents[3]

# Databases produced by the database layer
STRUCTURED_DB = ROOT / "src/database/structured_db/structured.db"
VECTOR_DB = ROOT / "src/database/vector_db/vector.db"

# Embedding model (must match ingestion)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Vector tables, mapped to a human-readable source label
TABLE_SOURCE = {
    "youtube_documents": "youtube",
    "hackernews_documents": "hackernews",
    "research_documents": "research",
}
VECTOR_TABLES = list(TABLE_SOURCE.keys())

# Retrieval defaults
TOP_K = 5
RRF_K = 60          # reciprocal-rank-fusion constant used by the hybrid strategy
HYBRID_OVERFETCH = 3  # each sub-strategy fetches top_k * this before fusion
