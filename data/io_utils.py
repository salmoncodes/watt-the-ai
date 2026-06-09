"""
io_utils.py

Utility functions for reading and writing JSON data used across:
- preprocessing
- feature extraction
- database transfer pipelines

This module ensures consistent file handling across the project.
"""

import json
from pathlib import Path


def load_json(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_jsonl(path):
    path = Path(path)
    data = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def save_jsonl(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for item in data:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")


def ensure_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
