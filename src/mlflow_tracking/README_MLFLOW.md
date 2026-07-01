# MLflow Tracking

Lightweight, local MLflow tracking for watt-the-ai. Backed entirely by a
SQLite database and a local artifact folder -- no external services and no
`mlruns/` file-based backend.

## What this tracks

- **RAG query runs** -- logged via `log_rag_query()` (params, metrics, and
  artifacts for a single `run_agent(...)` call).
- **Database pipeline runs** -- logged via `log_pipeline_run()` /
  `run_tracked_pipeline.py` (a full run of `run_data_pipeline.py`: structured
  DB transfer, chunking, and vector DB transfer/embedding).

## Storage

| What | Where |
|---|---|
| Run/experiment metadata | `mlflow.db` (SQLite, project root) |
| Artifacts (JSON/text files, optional DB files) | `mlartifacts/` (project root) |

Both are local, generated files -- see `.gitignore` (`mlflow.db`,
`mlartifacts/`, `mlruns/`). Do not commit them.

## Commands

Run the existing database pipeline with MLflow tracking (manual use only --
this can be slow, since it re-embeds documents):

```bash
python src/mlflow_tracking/run_tracked_pipeline.py
```

Start the MLflow UI (long-running -- run it in its own terminal):

```bash
python src/mlflow_tracking/run_mlflow_ui.py
```

Then open:

```
http://127.0.0.1:5000
```

## Experiments

- **`watt-the-ai-rag`** -- one run per RAG query (query text, retrieval
  strategy, top_k, latency, answer/prompt/grounding-check artifacts, etc.).
- **`watt-the-ai-pipeline`** -- one run per database pipeline execution
  (runtime, return code, DB row counts/sizes before and after, stdout/stderr).

## Notes

- Streamlit (when re-added) will call `log_rag_query()` after each query --
  no other integration is required.
- Database files (`structured.db`, `vector.db`) are **not** logged as
  artifacts by default because they can be large. Set `LOG_DB_ARTIFACTS=1`
  before running `run_tracked_pipeline.py` to include them.
- Do not commit `mlflow.db` or `mlartifacts/`.
