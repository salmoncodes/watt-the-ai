"""
sentiment_analysis_hackernews.py

Performs sentiment analysis on Hacker News discussions using VADER.
"""

from pathlib import Path

from utils.load_data import load_json
from utils.save_data import save_json
from models.vader_model import analyze_sentiment


PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")

INPUT_FILE = PROCESSED_DATA_DIR / "clean_hackernews.json"
OUTPUT_FILE = OUTPUT_DIR / "hackernews_sentiment_results.json"


def run_sentiment_analysis_hackernews():
    records = load_json(INPUT_FILE)

    results = []

    for record in records:
        text = record.get("text_clean", "")
        if not text:
            continue

        sentiment = analyze_sentiment(text)

        results.append({
            "record_id": record["record_id"],
            "story_id": record.get("story_id", ""),
            "author": record.get("author", ""),
            "text_length": len(text),

            "negative": sentiment["negative"],
            "neutral": sentiment["neutral"],
            "positive": sentiment["positive"],
            "compound": sentiment["compound"],
            "sentiment_label": sentiment["label"],

            "points": record.get("points"),
            "num_comments": record.get("num_comments"),
            "created_at": record.get("created_at", "")
        })

    save_json(OUTPUT_FILE, results)
    print(f"Sentiment analyzed for {len(results):,} Hacker News records")


if __name__ == "__main__":
    run_sentiment_analysis_hackernews()
