"""
services.py

Thin, safe wrappers around the existing backend modules: the RAG agent
(agentic_orchestration.graph.run_agent), MLflow tracking
(mlflow_tracking.tracking), and the drift-detection config (for sidebar
command/experiment display only). No RAG/MLflow/drift logic is
implemented here -- this module only imports and calls the existing,
unmodified code so the rest of app/ui/ doesn't need to know those import
paths.
"""

from agentic_orchestration.graph import run_agent
from mlflow_tracking.tracking import (
    log_rag_query,
    collect_database_status,
    get_tracking_paths,
)

try:
    from mlflow_tracking.drift.config import DRIFT_EXPERIMENT_NAME, DEFAULT_BASELINE_PATH
except Exception:
    DRIFT_EXPERIMENT_NAME = "watt-the-ai-drift"
    DEFAULT_BASELINE_PATH = None


def call_run_agent(query, no_llm, top_k, strategy_override):
    """Run the RAG agent. Behavior/signature preserved exactly from graph.run_agent()."""
    return run_agent(query, no_llm=no_llm, top_k=top_k, strategy_override=strategy_override)


def call_log_rag_query(query, result, latency_seconds, settings):
    """Log one RAG query run to MLflow. Raises on failure -- callers decide how to handle it."""
    return log_rag_query(query=query, result=result, latency_seconds=latency_seconds, settings=settings)


def check_database_status():
    """Wraps collect_database_status() so a broken DB layer can never crash the UI."""
    try:
        return collect_database_status()
    except Exception as exc:
        empty = {"exists": False, "path": None, "size_mb": None, "tables": {}, "note": str(exc)}
        return {"structured_db": dict(empty), "vector_db": dict(empty)}


def get_mlflow_tracking_paths():
    """Wraps get_tracking_paths(); returns None instead of raising if unavailable."""
    try:
        return get_tracking_paths()
    except Exception:
        return None
