"""
Drift detection package for watt-the-ai.

A lightweight, explainable "alarm system" that compares a saved baseline
snapshot of the project's databases and retrieval behavior against a
freshly collected current snapshot. See runner.py for the two top-level
entry points and README_MLFLOW.md for usage.
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
