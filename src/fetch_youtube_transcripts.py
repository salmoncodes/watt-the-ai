import argparse
import csv
import json
from pathlib import Path

from scrape_youtube_comments import load_video_ids


def get_transcript(video_id: str, languages: list[str]) -> dict:
    try:
        from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled
        from youtube_transcript_api import YouTubeTranscriptApi
    except ModuleNotFoundError as error:
        raise SystemExit("Missing youtube-transcript-api. Run: pip install -r requirements.txt") from error

    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages)
        segments = [
            {
                "text": segment.text,
                "start": segment.start,
                "duration": segment.duration,
            }
            for segment in transcript
        ]
        return {
            "video_id": video_id,
            "status": "ok",
            "language_attempted": languages,
            "segments": segments,
            "text": " ".join(segment["text"] for segment in segments),
        }
    except (NoTranscriptFound, TranscriptsDisabled) as error:
        return {
            "video_id": video_id,
            "status": "missing",
            "language_attempted": languages,
            "error": str(error),
            "segments": [],
            "text": "",
        }
    except Exception as error:
        return {
            "video_id": video_id,
            "status": "error",
            "language_attempted": languages,
            "error": str(error),
            "segments": [],
            "text": "",
        }


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
    parser = argparse.ArgumentParser(description="Fetch available YouTube transcripts.")
    parser.add_argument("--video-ids", type=Path, default=Path("config/video_ids.txt"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/youtube_transcripts.json"))
    parser.add_argument("--languages", nargs="+", default=["en"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    video_ids = load_video_ids(args.video_ids)
    if not video_ids:
        raise SystemExit(f"No video IDs found in {args.video_ids}.")

    records = [get_transcript(video_id, args.languages) for video_id in video_ids]
    save_records(records, args.output)

    ok_count = sum(1 for record in records if record["status"] == "ok")
    print(f"Saved {ok_count:,}/{len(records):,} transcripts to {args.output}")


if __name__ == "__main__":
    main()
