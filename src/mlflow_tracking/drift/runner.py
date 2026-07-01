"""
runner.py

Top-level orchestration for the drift package -- the public API used by
run_drift_check.py. Combines snapshot collection, baseline persistence,
comparison, reporting, and MLflow logging into the two commands:

- run_create_baseline(...)
- run_drift_check(...)
"""

import json
from pathlib import Path

from mlflow_tracking.drift.config import DEFAULT_BASELINE_PATH, DRIFT_EXPERIMENT_NAME
from mlflow_tracking.drift.snapshot import _collect_snapshot, collect_current_snapshot
from mlflow_tracking.drift.baseline import BaselineExistsError, save_baseline, load_baseline
from mlflow_tracking.drift.compare import build_drift_report
from mlflow_tracking.drift.reporting import build_summary_text
from mlflow_tracking.drift.mlflow_logger import log_drift_to_mlflow


def run_create_baseline(baseline_path=None, force=False):
    """Collect a snapshot and save it as the baseline. Prints status; never raises."""
    baseline_path = Path(baseline_path) if baseline_path else DEFAULT_BASELINE_PATH

    if baseline_path.exists() and not force:
        print(f"Baseline already exists at: {baseline_path}")
        print("Refusing to overwrite. Use --force to overwrite it:")
        print("  python src/mlflow_tracking/run_drift_check.py --create-baseline --force")
        return {"ok": False, "created": False, "path": str(baseline_path)}

    print("Collecting current project snapshot for baseline...")
    snapshot = _collect_snapshot("baseline")

    try:
        save_baseline(snapshot, baseline_path, force=force)
    except BaselineExistsError:
        print(f"Baseline already exists at: {baseline_path}")
        print("Refusing to overwrite. Use --force to overwrite it:")
        print("  python src/mlflow_tracking/run_drift_check.py --create-baseline --force")
        return {"ok": False, "created": False, "path": str(baseline_path)}

    run_id = log_drift_to_mlflow(None, None, snapshot, str(baseline_path), created_baseline=True)

    print("Baseline created.")
    print(f"Saved to: {baseline_path}")
    print(f"MLflow experiment: {DRIFT_EXPERIMENT_NAME}")
    print(f"MLflow run id: {run_id}")

    return {"ok": True, "created": True, "path": str(baseline_path), "run_id": run_id, "snapshot": snapshot}


def run_drift_check(baseline_path=None, output_json=False):
    """Load the baseline, collect a current snapshot, compare, log, and print. Never raises."""
    baseline_path = Path(baseline_path) if baseline_path else DEFAULT_BASELINE_PATH

    baseline = load_baseline(baseline_path)
    if baseline is None:
        print("No baseline found. Create one first with:")
        print("python src/mlflow_tracking/run_drift_check.py --create-baseline")
        return {"ok": False, "reason": "no_baseline"}

    print("Collecting current project snapshot...")
    current = collect_current_snapshot()
    report = build_drift_report(baseline, current, baseline_path)
    summary_text = build_summary_text(report)

    run_id = log_drift_to_mlflow(report, baseline, current, str(baseline_path), created_baseline=False)
    report["mlflow_run_id"] = run_id

    if output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        print()
        print(summary_text)
        print()
        print(f"MLflow experiment: {DRIFT_EXPERIMENT_NAME}")
        print(f"MLflow run id: {run_id}")

    return {"ok": True, "report": report, "summary": summary_text, "run_id": run_id}
