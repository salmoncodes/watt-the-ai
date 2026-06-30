"""
run_data_pipeline.py

Final execution layer that loads:
- cleaned data
- feature extraction outputs

and transfers them into:
- structured SQLite DB
- vector SQLite DB (with embeddings)
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if not (ROOT / "src").exists() or not (ROOT / "data").exists():
    raise RuntimeError(f"Could not find project root from {__file__}")


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
    # STRUCTURED DATABASE
    # ----------------------------
    run_step(
        ["src/database/structured_db/transfer_to_structured.py"],
        "Structured Database Transfer"
    )

    # ----------------------------
    # CHUNKING (prepares documents for embedding)
    # ----------------------------
    run_step(
        ["src/database/vector_db/chunking.py", "--input-dir", "data/preprocessing"],
        "Chunking (build document units)"
    )

    # ----------------------------
    # VECTOR DATABASE
    # ----------------------------
    run_step(
        ["src/database/vector_db/transfer_to_vector.py"],
        "Vector Database Transfer (Embedding)"
    )

    print("\n" + "=" * 60)
    print("DATABASE PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
