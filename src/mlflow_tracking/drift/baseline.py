"""
baseline.py

Baseline snapshot persistence: save/load the baseline JSON file that all
drift checks compare against.
"""

import json
from pathlib import Path


class BaselineExistsError(Exception):
    """Raised by save_baseline() when a baseline already exists and force=False."""


def ensure_parent_dir(path):
    """Create the parent directory of `path` if it doesn't exist."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def save_baseline(snapshot, path, force=False):
    """Write `snapshot` as JSON to `path`. Raises BaselineExistsError if the
    file already exists and force is False."""
    path = Path(path)
    if path.exists() and not force:
        raise BaselineExistsError(str(path))
    ensure_parent_dir(path)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def load_baseline(path):
    """Load a baseline JSON file. Returns None (never raises) if missing/corrupt."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[drift_detection] warning: failed to load baseline '{path}': {exc}")
        return None
