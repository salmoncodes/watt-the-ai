"""
tracking.py

Central MLflow helper module for watt-the-ai.

Provides a small, safe wrapper around MLflow so RAG query runs and database
pipeline runs can be logged without ever crashing the caller. All public
logging functions catch their own exceptions, print a warning, and return
None on failure instead of raising.

Storage (local, SQLite-backed -- not the legacy file:./mlruns backend):
    mlflow.db       tracking metadata (experiments, runs, params, metrics)
    mlartifacts/    logged artifacts (text/JSON files, optional DB files)
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

import mlflow

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

TRACKING_DB = ROOT / "mlflow.db"
ARTIFACT_ROOT = ROOT / "mlartifacts"
TRACKING_URI = f"sqlite:///{TRACKING_DB.resolve().as_posix()}"

RAG_EXPERIMENT_NAME = "watt-the-ai-rag"
PIPELINE_EXPERIMENT_NAME = "watt-the-ai-pipeline"

# Streamlit's Use-LLM mode tracking (see app/ui/chat.py::process_query) -- logged
# individually as params, in addition to the full settings.json artifact, so
# they're queryable/filterable directly in the MLflow runs table.
EXTRA_SETTING_PARAM_KEYS = [
    "requested_use_llm",
    "effective_use_llm",
    "llm_available",
    "llm_missing_reason",
    "mode",
    "mode_label",
    "no_llm",
]

STRUCTURED_DB_PATH = ROOT / "src/database/structured_db/structured.db"
VECTOR_DB_PATH = ROOT / "src/database/vector_db/vector.db"

STRUCTURED_DB_TABLES = [
    "videos",
    "comments",
    "transcripts",
    "hackernews",
    "research_sources",
    "sentiment_results",
    "youtube_relations",
]
VECTOR_DB_TABLES = [
    "youtube_documents",
    "hackernews_documents",
    "research_documents",
]


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
def get_tracking_paths():
    """Return the local MLflow storage locations as a JSON-safe dict."""
    return {
        "tracking_db": str(TRACKING_DB),
        "artifact_root": str(ARTIFACT_ROOT),
        "tracking_uri": TRACKING_URI,
    }


def configure_mlflow():
    """Point the MLflow client at the local SQLite backend.

    Only configures the Python client (tracking URI + artifact directory).
    Does not start a run or the MLflow UI.
    """
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(TRACKING_URI)
    return get_tracking_paths()


def _ensure_experiment(experiment_name):
    """Get-or-create `experiment_name`, make it active, and return its id."""
    configure_mlflow()
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        artifact_location = (ARTIFACT_ROOT / experiment_name).resolve().as_uri()
        experiment_id = mlflow.create_experiment(
            experiment_name, artifact_location=artifact_location
        )
    else:
        experiment_id = experiment.experiment_id
    mlflow.set_experiment(experiment_name)
    return experiment_id


# ----------------------------------------------------------------------
# Safe logging primitives
# ----------------------------------------------------------------------
def _safe_log_param(key, value):
    """Log one param as a short string; never raises."""
    try:
        text = "None" if value is None else str(value)
        if len(text) > 500:
            text = text[:500]
        mlflow.log_param(key, text)
    except Exception as exc:
        print(f"[mlflow_tracking] warning: failed to log param '{key}': {exc}")


def _safe_log_metric(key, value):
    """Log one numeric metric; skips (without raising) if not numeric."""
    if value is None:
        return
    try:
        mlflow.log_metric(key, float(value))
    except (TypeError, ValueError):
        print(f"[mlflow_tracking] warning: skipping non-numeric metric '{key}'={value!r}")
    except Exception as exc:
        print(f"[mlflow_tracking] warning: failed to log metric '{key}': {exc}")


def _log_json_artifact(data, artifact_file):
    """Log `data` as a pretty-printed JSON artifact; never raises."""
    try:
        mlflow.log_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            artifact_file,
        )
    except Exception as exc:
        print(f"[mlflow_tracking] warning: failed to log json artifact '{artifact_file}': {exc}")


def _log_text_artifact(text, artifact_file):
    """Log `text` as a plain-text artifact; never raises."""
    try:
        mlflow.log_text("" if text is None else str(text), artifact_file)
    except Exception as exc:
        print(f"[mlflow_tracking] warning: failed to log text artifact '{artifact_file}': {exc}")


# ----------------------------------------------------------------------
# Source document helpers
# ----------------------------------------------------------------------
def serialize_source_document(doc):
    """Convert a source document (dict, or a retriever's dataclass/object) into
    a plain JSON-safe dict."""
    if isinstance(doc, dict):
        return {
            "document_id": doc.get("document_id"),
            "text": doc.get("text", ""),
            "score": doc.get("score"),
            "source": doc.get("source"),
            "strategy": doc.get("strategy"),
            "doc_type": doc.get("doc_type"),
            "metadata": doc.get("metadata", {}),
        }
    return {
        "document_id": getattr(doc, "document_id", None),
        "text": getattr(doc, "text", ""),
        "score": getattr(doc, "score", None),
        "source": getattr(doc, "source", None),
        "strategy": getattr(doc, "strategy", None),
        "doc_type": getattr(doc, "doc_type", None),
        "metadata": getattr(doc, "metadata", {}),
    }


def extract_source_documents(result):
    """Return the richest available list of source documents for logging.

    Prefers result["source_documents"] (already dicts). Falls back to
    result["docs"] (possibly dataclass/object documents), serializing each
    one. Never relies on result["sources"] alone, since that may only be a
    list of document IDs.
    """
    result = result or {}

    source_documents = result.get("source_documents")
    if isinstance(source_documents, list):
        return source_documents

    docs = result.get("docs")
    if isinstance(docs, list):
        return [serialize_source_document(d) for d in docs]

    return []


# ----------------------------------------------------------------------
# Database status
# ----------------------------------------------------------------------
def _describe_db(db_path, tables):
    info = {
        "path": str(db_path),
        "exists": db_path.exists(),
        "size_mb": None,
        "tables": {},
    }
    if not db_path.exists():
        info["note"] = "database file not found"
        return info

    try:
        info["size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 4)
    except OSError as exc:
        info["note"] = f"could not stat file: {exc}"

    try:
        conn = sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        info["note"] = f"could not open database: {exc}"
        return info

    try:
        for table in tables:
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                info["tables"][table] = row[0] if row else None
            except sqlite3.Error:
                info["tables"][table] = None
    finally:
        conn.close()

    return info


def collect_database_status():
    """Return a JSON-safe snapshot of DB existence, size, and row counts.

    Never raises: a missing database file or table is recorded in the
    result rather than causing an error.
    """
    return {
        "structured_db": _describe_db(STRUCTURED_DB_PATH, STRUCTURED_DB_TABLES),
        "vector_db": _describe_db(VECTOR_DB_PATH, VECTOR_DB_TABLES),
    }


# ----------------------------------------------------------------------
# RAG query logging
# ----------------------------------------------------------------------
def log_rag_query(
    query,
    result,
    latency_seconds=None,
    settings=None,
    experiment_name=RAG_EXPERIMENT_NAME,
):
    """Log one RAG query run to MLflow.

    Safe to call from any caller (e.g. a future Streamlit app): all
    failures are caught, printed as a warning, and result in a None
    return instead of an exception.

    Returns the MLflow run id on success, or None if logging failed.
    """
    try:
        return _log_rag_query(query, result, latency_seconds, settings, experiment_name)
    except Exception as exc:
        print(f"[mlflow_tracking] warning: log_rag_query failed: {exc}")
        return None


def _log_rag_query(query, result, latency_seconds, settings, experiment_name):
    result = result or {}
    settings = settings or {}

    _ensure_experiment(experiment_name)

    query_preview = (query or "").strip()[:60]
    run_name = f"rag_query_{query_preview}" if query_preview else "rag_query"

    source_documents = extract_source_documents(result)
    sources = result.get("sources") if isinstance(result.get("sources"), list) else []
    plan = result.get("plan") if isinstance(result.get("plan"), dict) else {}
    filters = result.get("filters") if isinstance(result.get("filters"), dict) else {}

    embedding_model = None
    try:
        from rag.config.rag_config import EMBEDDING_MODEL
        embedding_model = EMBEDDING_MODEL
    except Exception:
        embedding_model = None

    with mlflow.start_run(run_name=run_name):
        _safe_log_param("query_preview", query_preview)
        _safe_log_param("retrieval_strategy", result.get("strategy"))
        _safe_log_param("top_k", settings.get("top_k"))
        _safe_log_param("use_llm", settings.get("use_llm"))
        _safe_log_param("strategy_override", settings.get("strategy_override"))
        _safe_log_param("source_filter", filters.get("source"))
        _safe_log_param("embedding_model", embedding_model)
        _safe_log_param("big_llm_model", os.getenv("RAG_BIG_LLM_MODEL"))
        _safe_log_param("small_llm_model", os.getenv("RAG_SMALL_LLM_MODEL"))
        _safe_log_param("structured_db_exists", STRUCTURED_DB_PATH.exists())
        _safe_log_param("vector_db_exists", VECTOR_DB_PATH.exists())
        _safe_log_param("task", plan.get("task"))
        for key in EXTRA_SETTING_PARAM_KEYS:
            _safe_log_param(key, settings.get(key))

        _safe_log_metric("latency_seconds", latency_seconds)
        _safe_log_metric("num_source_documents", len(source_documents))
        _safe_log_metric("num_sources", len(sources))
        _safe_log_metric("answer_length", len(result.get("answer") or ""))
        _safe_log_metric("prompt_length", len(result.get("prompt") or ""))
        _safe_log_metric("grounding_check_length", len(result.get("grounding_check") or ""))

        _log_text_artifact(result.get("answer"), "answer.txt")
        _log_text_artifact(result.get("prompt"), "prompt.txt")
        _log_text_artifact(result.get("grounding_check"), "grounding_check.txt")
        _log_json_artifact(source_documents, "source_documents.json")
        _log_json_artifact(sources, "sources.json")
        _log_json_artifact(filters, "filters.json")
        _log_json_artifact(plan, "plan.json")
        _log_json_artifact(result, "full_result.json")
        _log_json_artifact(settings, "settings.json")

        run_id = mlflow.active_run().info.run_id

    return run_id


# ----------------------------------------------------------------------
# Database pipeline run logging
# ----------------------------------------------------------------------
def log_pipeline_run(
    pipeline_name,
    status,
    runtime_seconds=None,
    metrics=None,
    params=None,
    artifacts=None,
    experiment_name=PIPELINE_EXPERIMENT_NAME,
):
    """Log a database pipeline run to MLflow.

    Generic helper used by run_tracked_pipeline.py. Never raises: failures
    are caught, printed as a warning, and result in a None return.

    Returns the MLflow run id on success, or None if logging failed.
    """
    try:
        return _log_pipeline_run(
            pipeline_name, status, runtime_seconds, metrics, params, artifacts, experiment_name
        )
    except Exception as exc:
        print(f"[mlflow_tracking] warning: log_pipeline_run failed: {exc}")
        return None


def _log_pipeline_artifact(artifact_file, value):
    try:
        if isinstance(value, (str, Path)) and Path(value).exists() and Path(value).is_file():
            mlflow.log_artifact(str(value))
        elif isinstance(value, (dict, list)):
            _log_json_artifact(value, artifact_file)
        else:
            _log_text_artifact(value, artifact_file)
    except Exception as exc:
        print(f"[mlflow_tracking] warning: failed to log pipeline artifact '{artifact_file}': {exc}")


def _log_pipeline_run(pipeline_name, status, runtime_seconds, metrics, params, artifacts, experiment_name):
    metrics = metrics or {}
    params = params or {}
    artifacts = artifacts or {}

    _ensure_experiment(experiment_name)

    with mlflow.start_run(run_name=pipeline_name):
        mlflow.set_tag("status", status)
        _safe_log_param("pipeline_name", pipeline_name)
        for key, value in params.items():
            _safe_log_param(key, value)

        _safe_log_metric("runtime_seconds", runtime_seconds)
        for key, value in metrics.items():
            _safe_log_metric(key, value)

        for artifact_file, value in artifacts.items():
            _log_pipeline_artifact(artifact_file, value)

        run_id = mlflow.active_run().info.run_id

    return run_id
