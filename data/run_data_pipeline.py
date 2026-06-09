"""
run_data_pipeline.py

Orchestrates the full end-to-end data pipeline:

1. YouTube extraction (assumed already run externally or via scripts)
2. Preprocessing layer
3. Feature extraction layer
4. Structured database transfer
5. Vector database transfer (with embeddings)

This script ensures reproducibility of the entire data workflow.
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_step(command, step_name):
    print("\n" + "=" * 60)
    print(f"RUNNING: {step_name}")
    print("=" * 60)

    result = subprocess.run([sys.executable] + command, cwd=ROOT)

    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {step_name}")

    print(f"COMPLETED: {step_name}")


def main():
    # ----------------------------
    # PREPROCESSING LAYER
    # ----------------------------
    run_step(
        ["preprocessing/run_all.py"],
        "Preprocessing Pipeline"
    )

    # ----------------------------
    # FEATURE EXTRACTION LAYER
    # ----------------------------
    run_step(
        ["feature_extraction/run_all.py"],
        "Feature Extraction Pipeline"
    )

    # ----------------------------
    # STRUCTURED DATABASE
    # ----------------------------
    run_step(
        ["database/structured_db/transfer_to_structured.py"],
        "Structured Database Transfer"
    )

    # ----------------------------
    # VECTOR DATABASE (WITH EMBEDDINGS)
    # ----------------------------
    run_step(
        ["database/vector_db/transfer_to_vector.py"],
        "Vector Database Transfer (Embedding)"
    )

    print("\n" + "=" * 60)
    print("FULL PIPELINE EXECUTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
