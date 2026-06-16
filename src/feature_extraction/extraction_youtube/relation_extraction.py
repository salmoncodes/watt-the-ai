"""
relation_extraction.py

Performs relation extraction on cleaned YouTube data using REBEL.

Input:
    data/preprocessing/clean_comments.json
    data/preprocessing/clean_transcripts.json

Output:
    data/feature_extraction/youtube_relation_results.json
"""


from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from models.rebel_model import analyze_relations


PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")
COMMENTS_FILE = PROCESSED_DATA_DIR / "clean_comments.json"
TRANSCRIPTS_FILE = PROCESSED_DATA_DIR / "clean_transcripts.json"
OUTPUT_FILE = OUTPUT_DIR / "youtube_relation_results.json"

def process_comments(comments):
    results = []
    for comment in comments:
        text = comment.get("text_clean", "")
        if not text:
            continue
        relations = analyze_relations(text)
        results.append({
            "source_type": "comment",
            "video_id": comment.get("video_id", ""),
            "document_id": comment.get("comment_id", ""),
            "text_clean": text,
            "relation_count": relations["relation_count"],
            "relations": relations["relations"]
        })
    return results

def process_transcripts(transcripts):
    results = []
    for transcript in transcripts:
        text = transcript.get("text_clean", "")
        if not text:
            continue
        relations = analyze_relations(text)
        results.append({
            "source_type": "transcript",
            "video_id": transcript.get("video_id", ""),
            "document_id": transcript.get("video_id", ""),
            "text_clean": text,
            "relation_count": relations["relation_count"],
            "relations": relations["relations"]
        })
    return results

def run_relation_extraction():
    comments = load_json(COMMENTS_FILE)
    transcripts = load_json(TRANSCRIPTS_FILE)
    results = []
    results.extend(process_comments(comments))
    results.extend(process_transcripts(transcripts))
    save_json(OUTPUT_FILE, results)
    print(f"Extracted relations from {len(results):,} YouTube documents")



if __name__ == "__main__":
    run_relation_extraction()
