"""
load_data.py

Utility functions for loading data files.

Used by:
    sentiment_analysis.py
    ner_extraction.py
    keyword_extraction.py
    topic_modeling.py
"""

import json
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            records.append(json.loads(line))
    return records


def load_file(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        return load_json(path)
    if path.suffix.lower() == ".jsonl":
        return load_jsonl(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")
