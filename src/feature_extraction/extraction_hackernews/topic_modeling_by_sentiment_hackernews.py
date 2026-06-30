"""
topic_modeling_by_sentiment_hackernews.py

Performs topic modeling grouped by sentiment on Hacker News
discussions using BERTopic.

Input:
    feature_extraction/output/hackernews_sentiment_results.json
Output:
    feature_extraction/output/hackernews_topic_by_sentiment_results.json
"""

from collections import defaultdict
from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from models.bertopic_model import analyze_batch

FEATURE_DIR = Path("data/feature_extraction")
PREP_DIR = Path("data/preprocessing")
INPUT_FILE = FEATURE_DIR / "hackernews_sentiment_results.json"
TEXT_FILE = PREP_DIR / "clean_hackernews.json"
OUTPUT_FILE = FEATURE_DIR / "hackernews_topic_by_sentiment_results.json"

def run_topic_modeling_by_sentiment_hackernews():
    records = load_json(INPUT_FILE)
    text_rows = load_json(TEXT_FILE)
    text_by_id = {row.get("record_id"): row for row in text_rows}
    sentiment_groups = defaultdict(list)
    for record in records:
        clean_row = text_by_id.get(record.get("record_id"), {})
        text = clean_row.get("text_clean", "").strip()
        if text:
            record["text_clean"] = text
            record["score"] = clean_row.get("points", 0) or 0
            sentiment_groups[record["sentiment_label"]].append(record)
    final_results = []
    for sentiment, records in sentiment_groups.items():
        texts = [record["text_clean"] for record in records]
        topic_results = analyze_batch(texts)
        topic_map = {}
        for i, topic in enumerate(topic_results):
            topic_id = topic["topic"]
            if topic_id == -1:
                continue
            if topic_id not in topic_map:
                topic_map[topic_id] = {
                    "sentiment_label": sentiment,
                    "topic": topic_id,
                    "count": 0,
                    "topic_words": topic["topic_words"],
                    "representative_posts": []
                }
            topic_map[topic_id]["count"] += 1
            topic_map[topic_id]["representative_posts"].append({
                "record_id": records[i]["record_id"],
                "story_id": records[i].get("story_id", ""),
                "text": records[i]["text_clean"],
                "compound": records[i]["compound"],
                "score": records[i].get("score", 0)
            })

        for topic in topic_map.values():
            topic["representative_posts"] = sorted(topic["representative_posts"], key=lambda x: x["score"], reverse=True)[:3]

        final_results.append({
            "sentiment_label": sentiment,
            "document_count": len(records),
            "topic_count": len(topic_map),
            "topics": sorted(topic_map.values(), key=lambda x: x["count"], reverse=True)})

    save_json(OUTPUT_FILE, final_results)
    print(f"Generated sentiment-based topics for {len(final_results)} Hacker News sentiment groups")

if __name__ == "__main__":
    run_topic_modeling_by_sentiment_hackernews()
