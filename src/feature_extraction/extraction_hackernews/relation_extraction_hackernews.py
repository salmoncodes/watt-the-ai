"""
relation_extraction_hackernews.py

Performs relation extraction on Hacker News discussions.

Input:
    data/preprocessing/clean_hackernews.json

Output:
    data/feature_extraction/hackernews_relation_results.json
"""

from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from models.rebel_model import analyze_relations

PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")
INPUT_FILE = PROCESSED_DATA_DIR / "clean_hackernews.json"
OUTPUT_FILE = OUTPUT_DIR / "hackernews_relation_results.json"

def run_relation_extraction_hackernews():
    records = load_json(INPUT_FILE)
    results = []
    for record in records:
        text = record.get("text_clean", "")
        if not text:
            continue
        relations = analyze_relations(text)
        results.append({
            "source": "hackernews",
            "record_id": record.get("record_id", ""),
            "story_id": record.get("story_id", ""),
            "author": record.get("author", ""),
            "text_clean": text,
            "relation_count": relations["relation_count"],
            "relations": relations["relations"]
        })
    save_json(OUTPUT_FILE, results)
    print(f"Extracted relations from {len(results):,} Hacker News records")


if __name__ == "__main__":
    run_relation_extraction_hackernews()
