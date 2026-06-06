"""
metadata_pipeline.py

Preprocesses YouTube video metadata.

Metadata is used for:
- Retrieval filtering
- Topic labeling
- Analytics
- Context augmentation in RAG

Only light text cleaning is applied.
"""

from pathlib import Path
from text_utils import *


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

INPUT_FILE = RAW_DATA_DIR / "youtube_videos.json"
OUTPUT_FILE = PROCESSED_DATA_DIR / "clean_videos.json"


def preprocess_metadata():

    videos = load_json(INPUT_FILE)
    processed = []

    for video in videos:

        # Clean title.
        title = normalize_unicode(video.get("title", ""))
        title = remove_noise(title)

        # Clean description.
        description = normalize_unicode(video.get("description", ""))
        description = remove_noise(description)

        processed.append({
            "video_id": video["video_id"],

            # Title fields.
            "title_original": video["title"],
            "title_clean": title,

            # Description fields.
            "description_original": video["description"],
            "description_clean": description,

            # Channel information.
            "channel_id": video["channel_id"],
            "channel_title": video["channel_title"],

            # Publication information.
            "published_at": video["published_at"],

            # Video metadata.
            "tags": video["tags"],
            "category_id": video["category_id"],
            "duration": video["duration"],
            "caption": video["caption"],

            # Engagement metrics.
            "view_count": video["view_count"],
            "like_count": video["like_count"],
            "comment_count": video["comment_count"]
        })

    save_json(OUTPUT_FILE, processed)

    print(f"Processed {len(processed):,} videos")


if __name__ == "__main__":
    preprocess_metadata()
