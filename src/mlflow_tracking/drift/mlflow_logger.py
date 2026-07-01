"""
mlflow_logger.py

All MLflow interaction for the drift package: experiment setup, safe
param/metric/artifact logging, and the top-level log_drift_to_mlflow()
used by both baseline-creation and drift-check runs.

Every logging call is wrapped so a logging failure never crashes the
drift checker -- it prints a warning and continues.
"""

import json

import mlflow

from mlflow_tracking.tracking import configure_mlflow
from mlflow_tracking.drift.config import (
    DRIFT_EXPERIMENT_NAME,
    DATABASE_COUNT_PERCENT_THRESHOLD,
    SENTIMENT_DRIFT_THRESHOLD,
    TOPIC_DRIFT_THRESHOLD,
    KEYWORD_JACCARD_THRESHOLD,
    RETRIEVAL_ZERO_SOURCE_THRESHOLD,
    RETRIEVAL_STRATEGY,
    RETRIEVAL_TOP_K,
    TEST_QUERIES,
)
from mlflow_tracking.drift.metrics import now_iso, safe_metric_name, bool_to_metric
from mlflow_tracking.drift.reporting import build_summary_text


def configure_drift_experiment():
    """Point MLflow at the local backend and activate the drift experiment."""
    configure_mlflow()
    try:
        from mlflow_tracking import tracking as _tracking_module
        _tracking_module._ensure_experiment(DRIFT_EXPERIMENT_NAME)
    except Exception:
        pass
    mlflow.set_experiment(DRIFT_EXPERIMENT_NAME)


def _safe_log_param(key, value):
    try:
        text = "None" if value is None else str(value)
        if len(text) > 500:
            text = text[:500]
        mlflow.log_param(key, text)
    except Exception as exc:
        print(f"[drift_detection] warning: failed to log param '{key}': {exc}")


def _safe_log_metric(key, value):
    if value is None:
        return
    try:
        mlflow.log_metric(safe_metric_name(key), float(value))
    except (TypeError, ValueError):
        print(f"[drift_detection] warning: skipping non-numeric metric '{key}'={value!r}")
    except Exception as exc:
        print(f"[drift_detection] warning: failed to log metric '{key}': {exc}")


def _log_json_artifact(data, artifact_file):
    try:
        mlflow.log_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), artifact_file)
    except Exception as exc:
        print(f"[drift_detection] warning: failed to log json artifact '{artifact_file}': {exc}")


def _log_text_artifact(text, artifact_file):
    try:
        mlflow.log_text("" if text is None else str(text), artifact_file)
    except Exception as exc:
        print(f"[drift_detection] warning: failed to log text artifact '{artifact_file}': {exc}")


def _log_common_params(baseline_path):
    _safe_log_param("baseline_path", baseline_path)
    _safe_log_param("created_at", now_iso())
    _safe_log_param("database_threshold_percent", DATABASE_COUNT_PERCENT_THRESHOLD)
    _safe_log_param("sentiment_threshold", SENTIMENT_DRIFT_THRESHOLD)
    _safe_log_param("topic_threshold", TOPIC_DRIFT_THRESHOLD)
    _safe_log_param("keyword_threshold", KEYWORD_JACCARD_THRESHOLD)
    _safe_log_param("retrieval_zero_source_threshold", RETRIEVAL_ZERO_SOURCE_THRESHOLD)
    _safe_log_param("retrieval_strategy", RETRIEVAL_STRATEGY)
    _safe_log_param("retrieval_top_k", RETRIEVAL_TOP_K)
    _safe_log_param("test_query_count", len(TEST_QUERIES))


def _log_database_drift_metrics(db_drift):
    if not db_drift.get("available"):
        return
    for prefix, section in (("structured", db_drift.get("structured", {})), ("vector", db_drift.get("vector", {}))):
        for table, info in section.items():
            base = f"{prefix}_{table}_count"
            _safe_log_metric(f"{base}_current", info.get("current_count"))
            _safe_log_metric(f"{base}_baseline", info.get("baseline_count"))
            _safe_log_metric(f"{base}_percent_change", info.get("percent_change"))
    _safe_log_metric("database_count_drift_alarm", bool_to_metric(db_drift.get("alarm")))


def _log_sentiment_drift_metrics(sd):
    _safe_log_metric("sentiment_available", bool_to_metric(sd.get("available")))
    if not sd.get("available"):
        return
    _safe_log_metric("sentiment_drift_score", sd.get("score"))
    _safe_log_metric("sentiment_drift_alarm", bool_to_metric(sd.get("alarm")))
    baseline_dist = sd.get("baseline_distribution", {})
    current_dist = sd.get("current_distribution", {})
    for label in sd.get("labels", []):
        safe_label = safe_metric_name(label)
        _safe_log_metric(f"sentiment_{safe_label}_baseline", baseline_dist.get(label))
        _safe_log_metric(f"sentiment_{safe_label}_current", current_dist.get(label))


def _log_topic_drift_metrics(td):
    _safe_log_metric("topic_available", bool_to_metric(td.get("available")))
    if not td.get("available"):
        return
    _safe_log_metric("topic_drift_score", td.get("score"))
    _safe_log_metric("topic_drift_alarm", bool_to_metric(td.get("alarm")))


def _log_keyword_drift_metrics(kd):
    _safe_log_metric("keyword_available", bool_to_metric(kd.get("available")))
    if not kd.get("available"):
        return
    _safe_log_metric("keyword_jaccard_distance", kd.get("jaccard_distance"))
    _safe_log_metric("keyword_tvd_score", kd.get("tvd_score"))
    _safe_log_metric("keyword_drift_alarm", bool_to_metric(kd.get("alarm")))


def _log_retrieval_drift_metrics(rd):
    _safe_log_metric("retrieval_available", bool_to_metric(rd.get("available")))
    if not rd.get("available"):
        return
    _safe_log_metric("retrieval_average_latency_baseline", rd.get("average_latency_baseline"))
    _safe_log_metric("retrieval_average_latency_current", rd.get("average_latency_current"))
    _safe_log_metric("retrieval_average_latency_percent_change", rd.get("average_latency_percent_change"))
    _safe_log_metric("retrieval_average_sources_baseline", rd.get("average_sources_baseline"))
    _safe_log_metric("retrieval_average_sources_current", rd.get("average_sources_current"))
    _safe_log_metric("retrieval_average_sources_percent_change", rd.get("average_sources_percent_change"))
    _safe_log_metric("retrieval_zero_source_rate_baseline", rd.get("zero_source_rate_baseline"))
    _safe_log_metric("retrieval_zero_source_rate_current", rd.get("zero_source_rate_current"))
    _safe_log_metric("retrieval_drift_alarm", bool_to_metric(rd.get("alarm")))


def _log_baseline_creation_metrics(snapshot):
    databases = snapshot.get("databases", {}) or {}
    for prefix in ("structured", "vector"):
        tables = (databases.get(prefix) or {}).get("tables", {}) or {}
        for table, count in tables.items():
            _safe_log_metric(f"{prefix}_{table}_count_baseline", count)

    sentiment = snapshot.get("sentiment", {}) or {}
    _safe_log_metric("sentiment_available", bool_to_metric(sentiment.get("available")))
    if sentiment.get("available"):
        for label, value in (sentiment.get("distribution") or {}).items():
            _safe_log_metric(f"sentiment_{safe_metric_name(label)}_baseline", value)

    topics = snapshot.get("topics", {}) or {}
    _safe_log_metric("topic_available", bool_to_metric(topics.get("available")))

    keywords = snapshot.get("keywords", {}) or {}
    _safe_log_metric("keyword_available", bool_to_metric(keywords.get("available")))

    retrieval = snapshot.get("retrieval", {}) or {}
    _safe_log_metric("retrieval_available", bool_to_metric(retrieval.get("available")))
    if retrieval.get("available"):
        _safe_log_metric("retrieval_average_latency_baseline", retrieval.get("average_latency_seconds"))
        _safe_log_metric("retrieval_average_sources_baseline", retrieval.get("average_source_documents"))
        _safe_log_metric("retrieval_zero_source_rate_baseline", retrieval.get("zero_source_rate"))


def log_drift_to_mlflow(report, baseline, current, baseline_path, created_baseline=False):
    """Log a baseline-creation run or a full drift-check run to MLflow.

    Never raises: any failure is caught, printed as a warning, and results
    in a None return so the caller can still print its terminal summary.
    """
    try:
        configure_drift_experiment()
    except Exception as exc:
        print(f"[drift_detection] warning: could not configure MLflow experiment: {exc}")
        return None

    run_name = "baseline_creation" if created_baseline else "drift_check"

    try:
        with mlflow.start_run(run_name=run_name):
            mlflow.set_tag("run_type", run_name)
            _log_common_params(baseline_path)

            if created_baseline:
                _log_json_artifact(current, "baseline_snapshot.json")
                _log_baseline_creation_metrics(current)
                _log_text_artifact(
                    f"Baseline created at {current.get('created_at')}\nSaved to: {baseline_path}",
                    "baseline_summary.txt",
                )
            else:
                _log_json_artifact(baseline, "baseline_snapshot.json")
                _log_json_artifact(current, "current_snapshot.json")
                _log_json_artifact(report, "drift_report.json")
                _log_text_artifact(build_summary_text(report), "drift_summary.txt")

                _log_database_drift_metrics(report.get("database_count_drift", {}))
                _log_sentiment_drift_metrics(report.get("sentiment_drift", {}))
                _log_topic_drift_metrics(report.get("topic_drift", {}))
                _log_keyword_drift_metrics(report.get("keyword_drift", {}))
                _log_retrieval_drift_metrics(report.get("retrieval_drift", {}))

                overall = report.get("overall", {})
                _safe_log_metric("overall_drift_alarm_count", overall.get("alarm_count"))
                _safe_log_metric("overall_drift_detected", bool_to_metric(overall.get("drift_detected")))

            run_id = mlflow.active_run().info.run_id
        return run_id
    except Exception as exc:
        print(f"[drift_detection] warning: failed to log drift run to MLflow: {exc}")
        return None
