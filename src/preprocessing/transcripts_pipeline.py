"""
transcripts_pipeline.py

Preprocesses YouTube transcripts.

Transcripts are primarily used for:
- RAG retrieval
- Topic modeling
- Summarization

Because transcripts are already structured,
they receive lighter preprocessing than comments.
"""

from pathlib import Path
from text_utils import *


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

INPUT_FILE = RAW_DATA_DIR / "youtube_transcripts_sample.json"
OUTPUT_FILE = PROCESSED_DATA_DIR / "clean_transcripts.json"


def preprocess_transcripts():

    transcripts = load_json(INPUT_FILE)
    processed = []

    for transcript in transcripts:

        # Skip unavailable transcripts.
        if transcript["status"] != "ok":
            continue

        text = transcript.get("text", "")

        if not text:
            continue

        # Light cleaning only.
        text = normalize_unicode(text)
        text = remove_noise(text)
        text = normalize_text(text)

        processed.append({
            "video_id": transcript["video_id"],
            "status": transcript["status"],
            "language_attempted": transcript["language_attempted"],

            # Preserve segment information
            # for future chunking and RAG.
            "segments": transcript["segments"],

            "segment_count": len(transcript["segments"]),
            "text_original": transcript["text"],
            "text_clean": text
        })

    save_json(OUTPUT_FILE, processed)

    print(f"Processed {len(processed):,} transcripts")


if __name__ == "__main__":
    preprocess_transcripts()
