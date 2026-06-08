"""
sentiment_analysis.py

Performs sentiment analysis on cleaned YouTube comments.

Input:
    data/preprocessing/clean_comments.json

Output:
    data/feature_extraction/sentiment_results.json
"""

from pathlib import Path

from utils.load_data import load_json
from utils.save_data import save_json
from models.vader_model import analyze_sentiment


PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")

INPUT_FILE = PROCESSED_DATA_DIR / "clean_comments.json"
OUTPUT_FILE = OUTPUT_DIR / "sentiment_results.json"


def run_sentiment_analysis():
    comments = load_json(INPUT_FILE)
    results = []
    for comment in comments:
        text = comment.get("text_clean", "")
        if not text:
            continue
        sentiment = analyze_sentiment(text)
        results.append({
            "video_id": comment["video_id"],
            "comment_id": comment["comment_id"],
            "parent_id": comment["parent_id"],
            "text_clean": text,

            "negative": sentiment["negative"],
            "neutral": sentiment["neutral"],
            "positive": sentiment["positive"],
            "compound": sentiment["compound"],
            "sentiment_label": sentiment["label"],

            "like_count": comment["like_count"],
            "published_at": comment["published_at"],
            "comment_type": comment["comment_type"]
        })
    save_json(OUTPUT_FILE, results)
    print(f"Analyzed sentiment for {len(results):,} comments")


if __name__ == "__main__":
    run_sentiment_analysis()
