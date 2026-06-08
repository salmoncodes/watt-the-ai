"""
ner_extraction.py

Performs Named Entity Recognition (NER) on
cleaned YouTube comments and transcripts.

Input:
    data/processed/clean_comments.json
    data/processed/clean_transcripts.json

Output:
    feature_extraction/output/ner_results.json
"""

from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from models.spacy_model import analyze_text


PROCESSED_DATA_DIR = Path("data/processed")
OUTPUT_DIR = Path("feature_extraction/output")
COMMENTS_FILE = PROCESSED_DATA_DIR / "clean_comments.json"
TRANSCRIPTS_FILE = PROCESSED_DATA_DIR / "clean_transcripts.json"
OUTPUT_FILE = OUTPUT_DIR / "ner_results.json"


def process_comments(comments):
    results = []
    for comment in comments:
        text = comment.get("text_clean", "")
        if not text:
            continue
        ner_result = analyze_text(text)
        results.append({
            "source_type": "comment",
            "video_id": comment["video_id"],
            "document_id": comment["comment_id"],
            "text_clean": text,
            "entity_count": ner_result["entity_count"],
            "entities": ner_result["entities"]
        })
    return results


def process_transcripts(transcripts):
    results = []
    for transcript in transcripts:
        text = transcript.get("text_clean", "")
        if not text:
            continue
        ner_result = analyze_text(text)
        results.append({
            "source_type": "transcript",
            "video_id": transcript["video_id"],
            "document_id": transcript["video_id"],
            "text_clean": text,
            "entity_count": ner_result["entity_count"],
            "entities": ner_result["entities"]
        })
    return results


def run_ner_extraction():
    comments = load_json(COMMENTS_FILE)
    transcripts = load_json(TRANSCRIPTS_FILE)
    results = []
    results.extend(process_comments(comments))
    results.extend(process_transcripts(transcripts))
    save_json(OUTPUT_FILE, results)
    print(f"Extracted entities from {len(results):,} documents")


if __name__ == "__main__":
    run_ner_extraction()
