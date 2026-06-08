"""
keyword_extraction.py

Performs keyword extraction using KeyBERT.

Input:
    data/processed/clean_videos.json
    data/processed/clean_transcripts.json
    data/processed/clean_comments.json

Output:
    feature_extraction/output/keyword_results.json
"""

from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from utils.text_merger import build_document_map
from models.keybert_model import analyze_text


PROCESSED_DATA_DIR = Path("data/processed")
OUTPUT_DIR = Path("feature_extraction/output")
VIDEOS_FILE = PROCESSED_DATA_DIR / "clean_videos.json"
TRANSCRIPTS_FILE = PROCESSED_DATA_DIR / "clean_transcripts.json"
COMMENTS_FILE = PROCESSED_DATA_DIR / "clean_comments.json"
OUTPUT_FILE = OUTPUT_DIR / "keyword_results.json"


def run_keyword_extraction():
    videos = load_json(VIDEOS_FILE)
    transcripts = load_json(TRANSCRIPTS_FILE)
    comments = load_json(COMMENTS_FILE)
    documents = build_document_map(videos, transcripts, comments)
    results = []
    for doc in documents:
        text = doc.get("text", "")
        if not text:
            continue
        keywords = analyze_text(text)
        results.append({
            "video_id": doc["video_id"],
            "text_length": len(text),
            "keyword_count": keywords["keyword_count"],
            "keywords": keywords["keywords"]
        })
    save_json(OUTPUT_FILE, results)
    print(f"Extracted keywords for {len(results):,} videos")


if __name__ == "__main__":
    run_keyword_extraction()

