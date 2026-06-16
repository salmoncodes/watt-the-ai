"""
topic_modeling.py

Performs topic modeling on YouTube comments and transcripts
using BERTopic.

Input:
    data/preprocessing/clean_comments.json
    data/preprocessing/clean_transcripts.json

Output:
    data/feature_extraction/topic_results.json
"""

from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from utils.text_merger import build_document_map
from models.bertopic_model import analyze_batch


PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")
COMMENTS_FILE = PROCESSED_DATA_DIR / "clean_comments.json"
TRANSCRIPTS_FILE = PROCESSED_DATA_DIR / "clean_transcripts.json"
VIDEOS_FILE = PROCESSED_DATA_DIR / "clean_videos.json"
OUTPUT_FILE = OUTPUT_DIR / "topic_results.json"


def run_topic_modeling():
    comments = load_json(COMMENTS_FILE)
    transcripts = load_json(TRANSCRIPTS_FILE)
    videos = load_json(VIDEOS_FILE)
    documents = build_document_map(videos, transcripts, comments)
    texts = [doc["text"] for doc in documents]
    topic_results = analyze_batch(texts)
    results = []
    for i in range(len(documents)):
        results.append({
            "video_id": documents[i]["video_id"],
            "text": documents[i]["text"],
            "topic": topic_results[i]["topic"],
            "probability": topic_results[i]["probability"]
        })
    save_json(OUTPUT_FILE, results)
    print(f"Generated topics for {len(results):,} documents")


if __name__ == "__main__":
    run_topic_modeling()
