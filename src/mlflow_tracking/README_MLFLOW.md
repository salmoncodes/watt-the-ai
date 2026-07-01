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
- **Drift detection runs** -- logged via `run_drift_check.py` (baseline
  creation and drift checks -- see [Drift detection](#drift-detection)
  below).

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

## Drift detection

A lightweight "alarm system" (`python src/mlflow_tracking/run_drift_check.py`)
that compares the current project data/behavior against a saved baseline
snapshot, computes simple drift metrics, and logs everything to MLflow.

Create a baseline (a snapshot of "known good" state, saved to
`mlflow_baselines/baseline_stats.json`):

```bash
python src/mlflow_tracking/run_drift_check.py --create-baseline
```

This refuses to overwrite an existing baseline unless you pass `--force`:

```bash
python src/mlflow_tracking/run_drift_check.py --create-baseline --force
```

Run a drift check against the saved baseline:

```bash
python src/mlflow_tracking/run_drift_check.py
```

Other options:

```bash
# Use a custom baseline file
python src/mlflow_tracking/run_drift_check.py --baseline-path path/to/baseline.json

# Print the full drift result as JSON instead of the text summary
python src/mlflow_tracking/run_drift_check.py --json
```

Open the MLflow UI (same command as above) and look for the
**`watt-the-ai-drift`** experiment:

```bash
python src/mlflow_tracking/run_mlflow_ui.py
```

### What it tracks

- **Database count drift** -- row counts for every table in `structured.db`
  and `vector.db`, baseline vs. current, flagged if any table's count
  changes by more than 30%.
- **Sentiment drift** -- label distribution from `sentiment_results` (or the
  first table/column that looks like sentiment), compared with Total
  Variation Distance (threshold 0.20).
- **Topic drift** -- topic distribution from the first topic table/column
  found (e.g. `topic_results`), compared with Total Variation Distance
  (threshold 0.30). Marked unavailable if no topic table exists.
- **Keyword drift** -- top-50 keyword sets, compared with Jaccard distance
  (threshold 0.50). Uses a real keyword table if one exists, otherwise falls
  back to simple stdlib word-frequency counting over comment/hackernews/
  research text columns (clearly marked `fallback_text_frequency`).
- **Retrieval behavior drift** -- runs a fixed set of 5 test queries through
  the RAG retriever in no-LLM / retrieval-only mode and compares average
  latency, average source-document count, and zero-source rate against the
  baseline.

All tables/columns are discovered dynamically via SQLite `PRAGMA` queries --
nothing is hardcoded to a specific schema, and a missing table/column marks
that section `unavailable` (with a reason) instead of crashing the script.

### What gets logged to MLflow (experiment `watt-the-ai-drift`)

- Params: threshold values, baseline path, retrieval strategy/top_k, etc.
- Metrics: per-table count drift, `sentiment_drift_score`,
  `topic_drift_score`, `keyword_jaccard_distance`, retrieval latency/source
  metrics, `overall_drift_alarm_count`, `overall_drift_detected` (1/0), etc.
- Artifacts: `baseline_snapshot.json`, `current_snapshot.json`,
  `drift_report.json`, `drift_summary.txt`.

### Honest scope

This is a lightweight, threshold-based drift monitoring system. It compares
current database and retrieval behavior against a saved baseline. It is
**not** a full production-grade monitoring system (no statistical
significance testing, no automated re-baselining, no alerting integration),
but it satisfies project-level drift monitoring and produces MLflow metrics
and artifacts that are easy to inspect and explain.

### Generated files (not committed)

- `mlflow_baselines/` -- baseline JSON snapshot(s).
- `drift_reports/` -- reserved for any local drift report exports.

Both are covered by `.gitignore`; MLflow artifacts (`mlartifacts/`) still
capture every snapshot/report per run for the record.

## Notes

- Streamlit (when re-added) will call `log_rag_query()` after each query --
  no other integration is required.
- Database files (`structured.db`, `vector.db`) are **not** logged as
  artifacts by default because they can be large. Set `LOG_DB_ARTIFACTS=1`
  before running `run_tracked_pipeline.py` to include them.
- Do not commit `mlflow.db` or `mlartifacts/`.
