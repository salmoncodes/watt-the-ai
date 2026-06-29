"""
embedder.py
Turns a query string into a vector using the SAME model used at ingestion time
(see transfer_to_vector.py), so the query lands in the same vector space as the
stored documents.

The model is loaded lazily on first use, so importing this module (or the
retrieval strategies that depend on it) does not require the model to be present
until an embedding is actually requested.
"""

from rag.config.rag_config import EMBEDDING_MODEL

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_query(text):
    """Return the query embedding as a plain list of floats (or None if empty)."""
    if not text:
        return None
    return _get_model().encode(text).tolist()
