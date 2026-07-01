"""
metrics.py

Small, reusable math/formatting helpers used across the drift package.

No SQLite, no MLflow -- just plain functions over plain Python values so
they're trivial to unit test and reason about.
"""

import re
from datetime import datetime, timezone


def safe_metric_name(name):
    """Sanitize a string into a safe MLflow metric/param key.

    Lowercase, underscores only, no spaces/slashes, bounded length.
    """
    text = str(name).strip().lower()
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = "metric"
    return text[:250]


def now_iso():
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def normalize_distribution(counts):
    """Convert {label: count} into {label: fraction_of_total}."""
    counts = counts or {}
    total = sum(v for v in counts.values() if isinstance(v, (int, float)))
    if total <= 0:
        return {}
    return {label: value / total for label, value in counts.items()}


def total_variation_distance(dist_a, dist_b):
    """0.5 * sum(|a - b|) over the union of labels. 0 if both distributions are empty."""
    dist_a = dist_a or {}
    dist_b = dist_b or {}
    labels = set(dist_a) | set(dist_b)
    if not labels:
        return 0.0
    return 0.5 * sum(abs(dist_a.get(label, 0.0) - dist_b.get(label, 0.0)) for label in labels)


def jaccard_distance(set_a, set_b):
    """1 - |intersection| / |union|. 0 if both sets are empty."""
    set_a = set(set_a or [])
    set_b = set(set_b or [])
    union = set_a | set_b
    if not union:
        return 0.0
    return 1 - (len(set_a & set_b) / len(union))


def percent_change(baseline, current):
    """Percent change from baseline to current, with explicit zero-baseline rules."""
    if baseline is None or current is None:
        return None
    if baseline == 0 and current == 0:
        return 0.0
    if baseline == 0 and current > 0:
        return 100.0
    return ((current - baseline) / baseline) * 100.0


def bool_to_metric(value):
    """Convert True/False/None into MLflow-friendly 1.0/0.0/None."""
    if value is None:
        return None
    return 1.0 if value else 0.0


def fmt(value, spec="{:.2f}", na="n/a"):
    """Format a possibly-None numeric value for human-readable text."""
    if value is None:
        return na
    try:
        return spec.format(value)
    except (TypeError, ValueError):
        return str(value)
