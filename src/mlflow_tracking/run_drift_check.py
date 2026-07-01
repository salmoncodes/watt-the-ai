"""
run_drift_check.py

CLI for the watt-the-ai drift alarm system. Thin wrapper around the
mlflow_tracking.drift package -- parses arguments, calls the right
function, prints the result, and exits 0 unless something truly
unexpected happens.

Usage:
    Create a baseline (fails if one already exists):
        python src/mlflow_tracking/run_drift_check.py --create-baseline

    Overwrite an existing baseline:
        python src/mlflow_tracking/run_drift_check.py --create-baseline --force

    Run a drift check against the saved baseline:
        python src/mlflow_tracking/run_drift_check.py

    Use a custom baseline file:
        python src/mlflow_tracking/run_drift_check.py --baseline-path path/to/baseline.json

    Print the drift result as JSON:
        python src/mlflow_tracking/run_drift_check.py --json
"""

import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mlflow_tracking.drift.config import DEFAULT_BASELINE_PATH
from mlflow_tracking.drift.runner import run_create_baseline, run_drift_check


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Watt-the-ai drift detection / alarm system.")
    parser.add_argument(
        "--create-baseline", action="store_true",
        help="Create a new baseline snapshot instead of running a drift check.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite an existing baseline (only used with --create-baseline).",
    )
    parser.add_argument(
        "--baseline-path", default=None,
        help=f"Custom baseline JSON path (default: {DEFAULT_BASELINE_PATH}).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the drift result as JSON instead of a human-readable summary.",
    )
    args = parser.parse_args()

    try:
        if args.create_baseline:
            result = run_create_baseline(baseline_path=args.baseline_path, force=args.force)
        else:
            result = run_drift_check(baseline_path=args.baseline_path, output_json=args.json)
    except Exception as exc:
        print(f"[run_drift_check] unexpected error: {exc}")
        raise SystemExit(1)

    if not result.get("ok"):
        raise SystemExit(0)


if __name__ == "__main__":
    main()
