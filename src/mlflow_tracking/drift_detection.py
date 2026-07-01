"""
drift_detection.py

Compatibility wrapper for the refactored drift detection package. The full
implementation now lives in src/mlflow_tracking/drift/ (config.py,
metrics.py, sqlite_utils.py, snapshot.py, retrieval_check.py, baseline.py,
compare.py, reporting.py, mlflow_logger.py, runner.py).

New code should import from mlflow_tracking.drift directly. This module is
kept only so any existing `from mlflow_tracking.drift_detection import ...`
imports keep working.
"""

from mlflow_tracking.drift.runner import run_create_baseline, run_drift_check
from mlflow_tracking.drift.snapshot import collect_current_snapshot
from mlflow_tracking.drift.compare import build_drift_report
from mlflow_tracking.drift.reporting import build_summary_text
from mlflow_tracking.drift.config import DRIFT_EXPERIMENT_NAME, DEFAULT_BASELINE_PATH

__all__ = [
    "run_create_baseline",
    "run_drift_check",
    "collect_current_snapshot",
    "build_drift_report",
    "build_summary_text",
    "DRIFT_EXPERIMENT_NAME",
    "DEFAULT_BASELINE_PATH",
]
