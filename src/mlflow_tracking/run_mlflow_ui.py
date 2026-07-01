"""
run_mlflow_ui.py

Launches the MLflow UI against the same local SQLite backend and artifact
root used by tracking.py (mlflow.db + mlartifacts/).

This is a long-running server -- it blocks the terminal until stopped
(Ctrl+C). Run it manually, in its own terminal.

Usage:
    python src/mlflow_tracking/run_mlflow_ui.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACKING_DB = ROOT / "mlflow.db"
ARTIFACT_ROOT = ROOT / "mlartifacts"

HOST = "127.0.0.1"
PORT = "5000"


def main():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

    tracking_uri = f"sqlite:///{TRACKING_DB.resolve().as_posix()}"
    artifact_root_uri = ARTIFACT_ROOT.resolve().as_posix()

    print("MLflow UI starting")
    print(f"Tracking DB: {TRACKING_DB}")
    print(f"Artifact root: {ARTIFACT_ROOT}")
    print(f"URL: http://{HOST}:{PORT}")

    subprocess.run(
        [
            sys.executable, "-m", "mlflow", "ui",
            "--backend-store-uri", tracking_uri,
            "--default-artifact-root", artifact_root_uri,
            "--host", HOST,
            "--port", PORT,
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    main()
