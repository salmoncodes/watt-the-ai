"""
run_tracked_pipeline.py

Runs the EXISTING database pipeline (src/database/execution/run_data_pipeline.py)
as a subprocess and logs the run to MLflow (experiment: watt-the-ai-pipeline).

This does not reimplement or modify the pipeline -- it wraps it so pipeline
runs get tracked (runtime, return code, stdout/stderr, DB status before/after).

Manual use only -- this can be slow, since the pipeline re-chunks documents
and regenerates embeddings.

Usage:
    python src/mlflow_tracking/run_tracked_pipeline.py

By default, the (potentially large) structured.db / vector.db files are NOT
uploaded as MLflow artifacts. Set LOG_DB_ARTIFACTS=1 to include them:

    LOG_DB_ARTIFACTS=1 python src/mlflow_tracking/run_tracked_pipeline.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlflow_tracking.tracking import (
    configure_mlflow,
    collect_database_status,
    log_pipeline_run,
    STRUCTURED_DB_PATH,
    VECTOR_DB_PATH,
)

PIPELINE_SCRIPT = ROOT / "src/database/execution/run_data_pipeline.py"
PIPELINE_NAME = "run_data_pipeline"


def _get_embedding_model():
    try:
        from rag.config.rag_config import EMBEDDING_MODEL
        return EMBEDDING_MODEL
    except Exception:
        return None


def main():
    tracking_paths = configure_mlflow()
    embedding_model = _get_embedding_model()

    db_status_before = collect_database_status()

    start = time.time()
    proc = subprocess.run(
        [sys.executable, str(PIPELINE_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    runtime_seconds = time.time() - start

    db_status_after = collect_database_status()
    status = "success" if proc.returncode == 0 else "failed"

    metrics = {"return_code": proc.returncode}

    structured_info = db_status_after.get("structured_db", {})
    vector_info = db_status_after.get("vector_db", {})
    if structured_info.get("size_mb") is not None:
        metrics["structured_db_size_mb"] = structured_info["size_mb"]
    if vector_info.get("size_mb") is not None:
        metrics["vector_db_size_mb"] = vector_info["size_mb"]

    vector_tables = vector_info.get("tables", {})
    table_to_metric = [
        ("youtube_documents", "vector_youtube_documents_count"),
        ("hackernews_documents", "vector_hackernews_documents_count"),
        ("research_documents", "vector_research_documents_count"),
    ]
    for table_name, metric_name in table_to_metric:
        count = vector_tables.get(table_name)
        if count is not None:
            metrics[metric_name] = count

    params = {
        "pipeline_script": str(PIPELINE_SCRIPT),
        "python_executable": sys.executable,
        "tracking_uri": tracking_paths["tracking_uri"],
        "embedding_model": embedding_model,
    }

    artifacts = {
        "pipeline_stdout.txt": proc.stdout,
        "pipeline_stderr.txt": proc.stderr,
        "db_status_before.json": db_status_before,
        "db_status_after.json": db_status_after,
    }

    if os.getenv("LOG_DB_ARTIFACTS") == "1":
        if STRUCTURED_DB_PATH.exists():
            artifacts["structured.db"] = STRUCTURED_DB_PATH
        if VECTOR_DB_PATH.exists():
            artifacts["vector.db"] = VECTOR_DB_PATH

    run_id = log_pipeline_run(
        pipeline_name=PIPELINE_NAME,
        status=status,
        runtime_seconds=runtime_seconds,
        metrics=metrics,
        params=params,
        artifacts=artifacts,
    )

    print(f"Pipeline status: {status}")
    print(f"Runtime: {runtime_seconds:.2f}s")
    print(f"Return code: {proc.returncode}")
    print(f"MLflow run id: {run_id}")

    if proc.stdout:
        print("\n--- pipeline stdout (tail) ---")
        print(proc.stdout[-2000:])
    if proc.stderr:
        print("\n--- pipeline stderr (tail) ---")
        print(proc.stderr[-2000:])

    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
