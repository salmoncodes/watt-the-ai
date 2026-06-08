"""
save_data.py

Utility functions for saving data files.

Used by:
    sentiment_analysis.py
    ner_extraction.py
    keyword_extraction.py
    topic_modeling.py
"""

import json
from pathlib import Path

def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def save_jsonl(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        for record in data:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_file(path, data):
    path = Path(path)
    if path.suffix.lower() == ".json":
        save_json(path, data)
        return
    if path.suffix.lower() == ".jsonl":
        save_jsonl(path, data)
        return
    raise ValueError(f"Unsupported file type: {path.suffix}")
