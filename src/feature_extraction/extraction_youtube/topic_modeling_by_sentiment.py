"""
topic_modeling_by_sentiment.py

Performs topic modeling grouped by sentiment using BERTopic.

Input:
    feature_extraction/output/sentiment_results.json

Output:
    feature_extraction/output/topic_by_sentiment_results.json
"""

from collections import defaultdict
from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from models.bertopic_model import analyze_batch

FEATURE_DIR = Path("feature_extraction/output")
INPUT_FILE = FEATURE_DIR / "sentiment_results.json"
OUTPUT_FILE = FEATURE_DIR / "topic_by_sentiment_results.json"

def run_topic_modeling():
    comments = load_json(INPUT_FILE)
    sentiment_groups = defaultdict(list)
    for comment in comments:
        text = comment.get("text_clean", "").strip()
        if text:
            sentiment_groups[comment["sentiment_label"]].append(comment)
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
                    "representative_comments": []
                }
              
            topic_map[topic_id]["count"] += 1
            topic_map[topic_id]["representative_comments"].append({
                "comment_id": records[i]["comment_id"],
                "video_id": records[i]["video_id"],
                "text": records[i]["text_clean"],
                "compound": records[i]["compound"],
                "like_count": records[i]["like_count"]
            })
          
        for topic in topic_map.values():
            topic["representative_comments"] = sorted(
                topic["representative_comments"],
                key=lambda x: x["like_count"],
                reverse=True
            )[:3]

        final_results.append({
            "sentiment_label": sentiment,
            "document_count": len(records),
            "topic_count": len(topic_map),
            "topics": sorted(
                topic_map.values(),
                key=lambda x: x["count"],
                reverse=True
            )})
      
    save_json(OUTPUT_FILE, final_results)
    print(f"Generated sentiment-based topics for {len(final_results)} sentiment groups")


if __name__ == "__main__":
    run_topic_modeling()
