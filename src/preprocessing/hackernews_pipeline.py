"""
hackernews_pipeline.py

Preprocesses optional Hacker News records for second-source sentiment analysis.

Input:
    data/raw/hackernews_discussions.json

Output:
    data/preprocessing/clean_hackernews.json
"""

from pathlib import Path
from text_utils import *


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/preprocessing")

INPUT_FILE = RAW_DATA_DIR / "hackernews_discussions.json"
OUTPUT_FILE = PROCESSED_DATA_DIR / "clean_hackernews.json"


def preprocess_hackernews():
    if not INPUT_FILE.exists():
        print(f"Skipping Hacker News preprocessing; missing {INPUT_FILE}")
        return

    records = load_json(INPUT_FILE)
    processed = []

    for record in records:

        text_original = record.get("text", "")

        if not text_original:
            continue

        text = normalize_unicode(text_original)
        text = remove_noise(text)
        text = convert_emojis(text)
        text = normalize_slang(text)
        text = normalize_text(text)

        if filter_language(text) is None:
            continue

        if is_spam(text):
            continue

        text_clean = text

        processed.append({
            "source": "hackernews",
            "record_id": record.get("record_id", ""),
            "story_id": record.get("story_id", ""),
            "parent_id": record.get("parent_id", ""),
            "author": record.get("author", ""),
            "title": record.get("title", ""),
            "url": record.get("url", ""),
            "text_original": text_original,
            "text_clean": text_clean,
            "points": record.get("points"),
            "num_comments": record.get("num_comments"),
            "created_at": record.get("created_at", ""),
            "query": record.get("query", ""),
        })

    processed = deduplicate(processed, ["record_id"])
    save_json(OUTPUT_FILE, processed)

    print(f"Processed {len(processed):,} Hacker News records")


if __name__ == "__main__":
    preprocess_hackernews()
