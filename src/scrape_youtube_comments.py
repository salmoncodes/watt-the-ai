import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Optional


def load_video_ids(path: Path) -> list[str]:
    video_ids: list[str] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue
        video_ids.append(line)
    return video_ids


def extract_comment_row(video_id: str, item: dict) -> dict:
    snippet = item["snippet"]
    top_comment = snippet["topLevelComment"]
    comment_snippet = top_comment["snippet"]

    return {
        "video_id": video_id,
        "comment_id": top_comment["id"],
        "parent_id": "",
        "author_display_name": comment_snippet.get("authorDisplayName", ""),
        "text_original": comment_snippet.get("textOriginal", ""),
        "text_display": comment_snippet.get("textDisplay", ""),
        "like_count": comment_snippet.get("likeCount", 0),
        "published_at": comment_snippet.get("publishedAt", ""),
        "updated_at": comment_snippet.get("updatedAt", ""),
        "total_reply_count": snippet.get("totalReplyCount", 0),
        "is_public": snippet.get("isPublic", True),
        "comment_type": "top_level",
    }


def extract_reply_row(video_id: str, parent_id: str, item: dict) -> dict:
    snippet = item["snippet"]

    return {
        "video_id": video_id,
        "comment_id": item["id"],
        "parent_id": parent_id,
        "author_display_name": snippet.get("authorDisplayName", ""),
        "text_original": snippet.get("textOriginal", ""),
        "text_display": snippet.get("textDisplay", ""),
        "like_count": snippet.get("likeCount", 0),
        "published_at": snippet.get("publishedAt", ""),
        "updated_at": snippet.get("updatedAt", ""),
        "total_reply_count": 0,
        "is_public": True,
        "comment_type": "reply",
    }


def fetch_top_level_comments(
    youtube,
    video_id: str,
    per_video_limit: Optional[int],
    request_pause: float,
) -> list[dict]:
    rows: list[dict] = []
    page_token = None

    while True:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            order="relevance",
            pageToken=page_token,
        )

        response = request.execute()
        rows.extend(extract_comment_row(video_id, item) for item in response.get("items", []))

        if per_video_limit and len(rows) >= per_video_limit:
            return rows[:per_video_limit]

        page_token = response.get("nextPageToken")
        if not page_token:
            return rows

        if request_pause:
            time.sleep(request_pause)


def fetch_replies(youtube, video_id: str, parent_id: str, request_pause: float) -> list[dict]:
    rows: list[dict] = []
    page_token = None

    while True:
        request = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=page_token,
        )
        response = request.execute()
        rows.extend(extract_reply_row(video_id, parent_id, item) for item in response.get("items", []))

        page_token = response.get("nextPageToken")
        if not page_token:
            return rows

        if request_pause:
            time.sleep(request_pause)


def scrape_comments(
    api_key: str,
    video_ids: list[str],
    target_total: int,
    per_video_limit: Optional[int],
    request_pause: float,
    include_replies: bool,
) -> list[dict]:
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Missing google-api-python-client. Run: pip install -r requirements.txt"
        ) from error

    try:
        from tqdm import tqdm
    except ModuleNotFoundError:
        tqdm = None

    youtube = build("youtube", "v3", developerKey=api_key)
    all_rows: list[dict] = []
    seen_comment_ids: set[str] = set()

    progress = tqdm(total=target_total, desc="comments") if tqdm else None
    try:
        for video_id in video_ids:
            if len(all_rows) >= target_total:
                break

            try:
                rows = fetch_top_level_comments(
                    youtube=youtube,
                    video_id=video_id,
                    per_video_limit=per_video_limit,
                    request_pause=request_pause,
                )
            except HttpError as error:
                print(f"Skipping {video_id}: {error}")
                continue

            added = 0
            for row in rows:
                comment_id = row["comment_id"]
                if comment_id in seen_comment_ids:
                    continue
                seen_comment_ids.add(comment_id)
                all_rows.append(row)
                added += 1
                if len(all_rows) >= target_total:
                    break

                if include_replies and row.get("total_reply_count", 0) > 0:
                    try:
                        replies = fetch_replies(youtube, video_id, comment_id, request_pause)
                    except HttpError as error:
                        print(f"Skipping replies for {comment_id}: {error}")
                        continue

                    for reply in replies:
                        reply_id = reply["comment_id"]
                        if reply_id in seen_comment_ids:
                            continue
                        seen_comment_ids.add(reply_id)
                        all_rows.append(reply)
                        added += 1
                        if len(all_rows) >= target_total:
                            break

                if len(all_rows) >= target_total:
                    break

            if progress:
                progress.update(added)
            else:
                print(f"{video_id}: added {added:,}; total {len(all_rows):,}")
    finally:
        if progress:
            progress.close()

    return all_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape top-level YouTube comments.")
    parser.add_argument("--video-ids", type=Path, default=Path("config/video_ids.txt"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/youtube_comments.json"))
    parser.add_argument("--target-total", type=int, default=40000)
    parser.add_argument("--per-video-limit", type=int, default=None)
    parser.add_argument("--request-pause", type=float, default=0.0)
    parser.add_argument("--include-replies", action="store_true")
    parser.add_argument("--api-key", default=os.getenv("YOUTUBE_API_KEY"))
    return parser.parse_args()


def save_comments(comments: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.suffix.lower() == ".csv":
        fieldnames = list(comments[0].keys()) if comments else []
        with output.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comments)
        return

    if output.suffix.lower() == ".jsonl":
        with output.open("w", encoding="utf-8") as file:
            for record in comments:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
        return

    with output.open("w", encoding="utf-8") as file:
        json.dump(comments, file, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Set YOUTUBE_API_KEY or pass --api-key.")

    video_ids = load_video_ids(args.video_ids)
    if not video_ids:
        raise SystemExit(f"No video IDs found in {args.video_ids}.")

    comments = scrape_comments(
        api_key=args.api_key,
        video_ids=video_ids,
        target_total=args.target_total,
        per_video_limit=args.per_video_limit,
        request_pause=args.request_pause,
        include_replies=args.include_replies,
    )

    save_comments(comments, args.output)
    print(f"Saved {len(comments):,} comments to {args.output}")


if __name__ == "__main__":
    main()
