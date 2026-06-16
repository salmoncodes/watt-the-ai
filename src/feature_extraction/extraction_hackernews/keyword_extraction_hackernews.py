"""
keyword_extraction_hackernews.py

Performs keyword extraction on Hacker News discussions using KeyBERT.

Input:
    data/preprocessing/clean_hackernews.json

Output:
    data/feature_extraction/hackernews_keyword_results.json
"""

from pathlib import Path

from utils.load_data import load_json
from utils.save_data import save_json
from models.keybert_model import analyze_text


PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")

INPUT_FILE = PROCESSED_DATA_DIR / "clean_hackernews.json"
OUTPUT_FILE = OUTPUT_DIR / "hackernews_keyword_results.json"


def run_keyword_extraction_hackernews():
    records = load_json(INPUT_FILE)

    results = []

    for record in records:
        text = record.get("text_clean", "")
        if not text:
            continue

        keywords = analyze_text(text)

        results.append({
            "record_id": record["record_id"],
            "story_id": record.get("story_id", ""),
            "author": record.get("author", ""),
            "text_length": len(text),
            "keyword_count": keywords["keyword_count"],
            "keywords": keywords["keywords"]
        })

    save_json(OUTPUT_FILE, results)
    print(f"Extracted keywords for {len(results):,} Hacker News records")


if __name__ == "__main__":
    run_keyword_extraction_hackernews()
