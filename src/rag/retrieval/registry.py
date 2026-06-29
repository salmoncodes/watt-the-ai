"""
registry.py
Name -> strategy mapping so the agent layer selects a retriever by name
("semantic", "lexical", "metadata", "hybrid") without importing the classes
directly. Instances are created lazily and cached, since some strategies build
indexes or open connections on construction.
"""

from rag.retrieval.semantic_retriever import SemanticRetriever
from rag.retrieval.lexical_retriever import LexicalRetriever
from rag.retrieval.metadata_retriever import MetadataRetriever
from rag.retrieval.hybrid_retriever import HybridRetriever

_FACTORIES = {
    "semantic": SemanticRetriever,
    "lexical": LexicalRetriever,
    "metadata": MetadataRetriever,
    "hybrid": HybridRetriever,
}
_CACHE = {}


def list_strategies():
    """Return the available strategy names."""
    return list(_FACTORIES)


def get_retriever(name):
    """Return a (cached) retriever instance for the given strategy name."""
    if name not in _FACTORIES:
        raise ValueError(f"Unknown retrieval strategy '{name}'. "
                         f"Available: {', '.join(_FACTORIES)}")
    if name not in _CACHE:
        _CACHE[name] = _FACTORIES[name]()
    return _CACHE[name]
