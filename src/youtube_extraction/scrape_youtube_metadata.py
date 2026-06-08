import argparse
import csv
import json
import os
from pathlib import Path

from scrape_youtube_comments import load_video_ids


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def extract_video_metadata(item: dict) -> dict:
    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})
    content_details = item.get("contentDetails", {})

    return {
        "video_id": item.get("id", ""),
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "tags": snippet.get("tags", []),
        "category_id": snippet.get("categoryId", ""),
        "duration": content_details.get("duration", ""),
        "caption": content_details.get("caption", ""),
        "view_count": int(statistics.get("viewCount", 0)),
        "like_count": int(statistics.get("likeCount", 0)),
        "comment_count": int(statistics.get("commentCount", 0)),
    }


def fetch_video_metadata(api_key: str, video_ids: list[str]) -> list[dict]:
    try:
        from googleapiclient.discovery import build
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Missing google-api-python-client. Run: pip install -r requirements.txt"
        ) from error

    youtube = build("youtube", "v3", developerKey=api_key)
    rows: list[dict] = []

    for batch in chunked(video_ids, 50):
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch),
            maxResults=50,
        )
        response = request.execute()
        rows.extend(extract_video_metadata(item) for item in response.get("items", []))

    return rows


def save_records(records: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.suffix.lower() == ".csv":
        fieldnames = list(records[0].keys()) if records else []
        with output.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        return

    if output.suffix.lower() == ".jsonl":
        with output.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
        return

    with output.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape YouTube video metadata.")
    parser.add_argument("--video-ids", type=Path, default=Path("config/video_ids.txt"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/youtube_videos.json"))
    parser.add_argument("--api-key", default=os.getenv("YOUTUBE_API_KEY"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Set YOUTUBE_API_KEY or pass --api-key.")

    video_ids = load_video_ids(args.video_ids)
    if not video_ids:
        raise SystemExit(f"No video IDs found in {args.video_ids}.")

    records = fetch_video_metadata(args.api_key, video_ids)
    save_records(records, args.output)
    print(f"Saved {len(records):,} video metadata records to {args.output}")


if __name__ == "__main__":
    main()

