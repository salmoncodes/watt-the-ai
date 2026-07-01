"""
compare.py

Drift comparison logic: baseline vs. current snapshot -> drift scores,
alarms, and the assembled drift_report.json dict.

No MLflow, no snapshot collection here -- pure comparison of already-
collected data.
"""

from mlflow_tracking.drift.config import (
    DATABASE_COUNT_PERCENT_THRESHOLD,
    SENTIMENT_DRIFT_THRESHOLD,
    TOPIC_DRIFT_THRESHOLD,
    KEYWORD_JACCARD_THRESHOLD,
    RETRIEVAL_ZERO_SOURCE_THRESHOLD,
    RETRIEVAL_SOURCE_DROP_PERCENT_THRESHOLD,
    RETRIEVAL_LATENCY_INCREASE_PERCENT_THRESHOLD,
)
from mlflow_tracking.drift.metrics import (
    now_iso,
    percent_change,
    normalize_distribution,
    total_variation_distance,
    jaccard_distance,
)


def compare_counts(baseline_tables, current_tables, prefix):
    """Per-table baseline vs. current row counts, with percent-change alarms."""
    baseline_tables = baseline_tables or {}
    current_tables = current_tables or {}
    result = {}
    alarms = []

    for table in sorted(set(baseline_tables) | set(current_tables)):
        baseline_count = baseline_tables.get(table)
        current_count = current_tables.get(table)

        if baseline_count is None or current_count is None:
            result[table] = {
                "baseline_count": baseline_count,
                "current_count": current_count,
                "absolute_change": None,
                "percent_change": None,
                "alarm": False,
                "reason": "count unavailable in baseline or current snapshot",
            }
            continue

        pct = percent_change(baseline_count, current_count)
        alarm = abs(pct) > DATABASE_COUNT_PERCENT_THRESHOLD
        if alarm:
            alarms.append(f"{prefix}.{table}")

        result[table] = {
            "baseline_count": baseline_count,
            "current_count": current_count,
            "absolute_change": current_count - baseline_count,
            "percent_change": pct,
            "alarm": alarm,
        }

    return result, alarms


def build_database_count_drift(baseline_databases, current_databases):
    baseline_databases = baseline_databases or {}
    current_databases = current_databases or {}

    baseline_structured = (baseline_databases.get("structured") or {}).get("tables", {}) or {}
    current_structured = (current_databases.get("structured") or {}).get("tables", {}) or {}
    baseline_vector = (baseline_databases.get("vector") or {}).get("tables", {}) or {}
    current_vector = (current_databases.get("vector") or {}).get("tables", {}) or {}

    structured_result, structured_alarms = compare_counts(baseline_structured, current_structured, "structured")
    vector_result, vector_alarms = compare_counts(baseline_vector, current_vector, "vector")
    alarms = structured_alarms + vector_alarms

    return {
        "available": True,
        "threshold_percent": DATABASE_COUNT_PERCENT_THRESHOLD,
        "structured": structured_result,
        "vector": vector_result,
        "alarm": len(alarms) > 0,
        "alarms": alarms,
    }


def compare_distribution_drift(baseline_section, current_section, threshold, category_label):
    """Generic TVD-based comparison, used for both sentiment and topic drift."""
    result = {
        "available": False,
        "reason": None,
        "source_table": None,
        "source_column": None,
        "score": None,
        "threshold": threshold,
        "alarm": False,
        "labels": [],
        "baseline_distribution": {},
        "current_distribution": {},
    }
    baseline_section = baseline_section or {}
    current_section = current_section or {}

    if not baseline_section.get("available"):
        result["reason"] = f"baseline {category_label} unavailable: {baseline_section.get('reason')}"
        return result
    if not current_section.get("available"):
        result["reason"] = f"current {category_label} unavailable: {current_section.get('reason')}"
        return result

    baseline_dist = baseline_section.get("distribution") or {}
    current_dist = current_section.get("distribution") or {}
    score = total_variation_distance(baseline_dist, current_dist)

    result.update({
        "available": True,
        "source_table": current_section.get("source_table") or baseline_section.get("source_table"),
        "source_column": current_section.get("source_column") or baseline_section.get("source_column"),
        "score": score,
        "alarm": score > threshold,
        "labels": sorted(set(baseline_dist) | set(current_dist)),
        "baseline_distribution": baseline_dist,
        "current_distribution": current_dist,
    })
    return result


def compare_keyword_drift(baseline_kw, current_kw, threshold):
    """Jaccard distance on top-keyword sets (+ TVD on frequencies, informational)."""
    result = {
        "available": False,
        "reason": None,
        "source": None,
        "source_table": None,
        "source_column": None,
        "jaccard_distance": None,
        "tvd_score": None,
        "threshold": threshold,
        "alarm": False,
        "baseline_top_terms": {},
        "current_top_terms": {},
    }
    baseline_kw = baseline_kw or {}
    current_kw = current_kw or {}

    if not baseline_kw.get("available"):
        result["reason"] = f"baseline keywords unavailable: {baseline_kw.get('reason')}"
        return result
    if not current_kw.get("available"):
        result["reason"] = f"current keywords unavailable: {current_kw.get('reason')}"
        return result

    baseline_terms = baseline_kw.get("top_terms") or {}
    current_terms = current_kw.get("top_terms") or {}
    jaccard = jaccard_distance(set(baseline_terms), set(current_terms))
    tvd = total_variation_distance(normalize_distribution(baseline_terms), normalize_distribution(current_terms))

    result.update({
        "available": True,
        "source": current_kw.get("source") or baseline_kw.get("source"),
        "source_table": current_kw.get("source_table") or baseline_kw.get("source_table"),
        "source_column": current_kw.get("source_column") or baseline_kw.get("source_column"),
        "jaccard_distance": jaccard,
        "tvd_score": tvd,
        "alarm": jaccard > threshold,
        "baseline_top_terms": baseline_terms,
        "current_top_terms": current_terms,
    })
    return result


def compare_retrieval_drift(baseline_retrieval, current_retrieval):
    result = {"available": False, "reason": None, "alarm": False}
    baseline_retrieval = baseline_retrieval or {}
    current_retrieval = current_retrieval or {}

    if not baseline_retrieval.get("available"):
        result["reason"] = f"retrieval baseline unavailable: {baseline_retrieval.get('reason')}"
        return result
    if not current_retrieval.get("available"):
        result["reason"] = f"retrieval current unavailable: {current_retrieval.get('reason')}"
        return result

    baseline_latency = baseline_retrieval.get("average_latency_seconds")
    current_latency = current_retrieval.get("average_latency_seconds")
    baseline_sources = baseline_retrieval.get("average_source_documents")
    current_sources = current_retrieval.get("average_source_documents")
    baseline_zero_rate = baseline_retrieval.get("zero_source_rate")
    current_zero_rate = current_retrieval.get("zero_source_rate")

    latency_pct = percent_change(baseline_latency, current_latency)
    sources_pct = percent_change(baseline_sources, current_sources)

    alarm = False
    if current_zero_rate is not None and current_zero_rate > RETRIEVAL_ZERO_SOURCE_THRESHOLD:
        alarm = True
    if sources_pct is not None and sources_pct < -RETRIEVAL_SOURCE_DROP_PERCENT_THRESHOLD:
        alarm = True
    if latency_pct is not None and latency_pct > RETRIEVAL_LATENCY_INCREASE_PERCENT_THRESHOLD:
        alarm = True

    result.update({
        "available": True,
        "average_latency_baseline": baseline_latency,
        "average_latency_current": current_latency,
        "average_latency_percent_change": latency_pct,
        "average_sources_baseline": baseline_sources,
        "average_sources_current": current_sources,
        "average_sources_percent_change": sources_pct,
        "zero_source_rate_baseline": baseline_zero_rate,
        "zero_source_rate_current": current_zero_rate,
        "alarm": alarm,
    })
    return result


def build_drift_report(baseline, current, baseline_path):
    """Assemble the full drift_report.json structure from baseline + current snapshots."""
    baseline = baseline or {}
    current = current or {}

    database_drift = build_database_count_drift(baseline.get("databases"), current.get("databases"))
    sentiment_drift = compare_distribution_drift(
        baseline.get("sentiment"), current.get("sentiment"), SENTIMENT_DRIFT_THRESHOLD, "sentiment"
    )
    topic_drift = compare_distribution_drift(
        baseline.get("topics"), current.get("topics"), TOPIC_DRIFT_THRESHOLD, "topic"
    )
    keyword_drift = compare_keyword_drift(
        baseline.get("keywords"), current.get("keywords"), KEYWORD_JACCARD_THRESHOLD
    )
    retrieval_drift = compare_retrieval_drift(baseline.get("retrieval"), current.get("retrieval"))

    alarms = []
    if database_drift.get("alarm"):
        alarms.append("database_count_drift")
    if sentiment_drift.get("alarm"):
        alarms.append("sentiment_drift")
    if topic_drift.get("alarm"):
        alarms.append("topic_drift")
    if keyword_drift.get("alarm"):
        alarms.append("keyword_drift")
    if retrieval_drift.get("alarm"):
        alarms.append("retrieval_drift")

    return {
        "created_at": now_iso(),
        "baseline_path": str(baseline_path),
        "baseline_created_at": baseline.get("created_at"),
        "database_count_drift": database_drift,
        "sentiment_drift": sentiment_drift,
        "topic_drift": topic_drift,
        "keyword_drift": keyword_drift,
        "retrieval_drift": retrieval_drift,
        "overall": {
            "drift_detected": len(alarms) > 0,
            "alarm_count": len(alarms),
            "alarms": alarms,
        },
    }
