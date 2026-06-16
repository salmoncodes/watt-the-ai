"""
topic_modeling_hackernews.py

Performs topic modeling on Hacker News discussions using BERTopic.
"""

from pathlib import Path

from utils.load_data import load_json
from utils.save_data import save_json
from models.bertopic_model import analyze_batch


PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")

INPUT_FILE = PROCESSED_DATA_DIR / "clean_hackernews.json"
OUTPUT_FILE = OUTPUT_DIR / "hackernews_topic_results.json"


def run_topic_modeling_hackernews():
    records = load_json(INPUT_FILE)

    texts = [r.get("text_clean", "") for r in records if r.get("text_clean", "")]

    topic_results = analyze_batch(texts)

    results = []

    idx = 0
    for record in records:
        text = record.get("text_clean", "")
        if not text:
            continue

        results.append({
            "record_id": record["record_id"],
            "story_id": record.get("story_id", ""),
            "text": text,
            "topic": topic_results[idx]["topic"],
            "probability": topic_results[idx]["probability"]
        })

        idx += 1

    save_json(OUTPUT_FILE, results)
    print(f"Generated topics for {len(results):,} Hacker News records")


if __name__ == "__main__":
    run_topic_modeling_hackernews()
