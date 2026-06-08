"""
comments_pipeline.py

Preprocesses YouTube comments for sentiment analysis.

Comments receive the most aggressive cleaning because
they contain:
- slang
- emojis
- spam
- informal language

Input:
    data/raw/youtube_comments.json

Output:
    data/preprocessing/clean_comments.json
"""

from pathlib import Path
from text_utils import *


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/preprocessing")

INPUT_FILE = RAW_DATA_DIR / "youtube_comments.json"
OUTPUT_FILE = PROCESSED_DATA_DIR / "clean_comments.json"


def preprocess_comments():

    comments = load_json(INPUT_FILE)
    processed = []

    for comment in comments:

        # Extract original comment text.
        text = comment.get("text_original", "")

        if not text:
            continue

        # Text cleaning pipeline.
        text = normalize_unicode(text)
        text = remove_noise(text)
        text = convert_emojis(text)
        text = normalize_slang(text)
        text = normalize_text(text)

        # Keep English comments only.
        text = filter_language(text)

        if text is None:
            continue

        # Remove spam.
        if is_spam(text):
            continue

        processed.append({
            "video_id": comment["video_id"],
            "comment_id": comment["comment_id"],
            "parent_id": comment["parent_id"],
            "author_display_name": comment["author_display_name"],
            "text_original": comment["text_original"],
            "text_clean": text,
            "like_count": comment["like_count"],
            "total_reply_count": comment["total_reply_count"],
            "published_at": comment["published_at"],
            "updated_at": comment["updated_at"],
            "comment_type": comment["comment_type"],
            "is_public": comment["is_public"]
        })

    processed = deduplicate(processed, ["video_id", "comment_id"])

    save_json(OUTPUT_FILE, processed)

    print(f"Processed {len(processed):,} comments")


if __name__ == "__main__":
    preprocess_comments()
