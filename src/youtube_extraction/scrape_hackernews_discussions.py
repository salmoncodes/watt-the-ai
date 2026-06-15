import argparse
import json
import time
from pathlib import Path

import requests


HN_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"


def load_queries(path: Path) -> list[str]:
    queries: list[str] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        queries.append(line)
    return queries


def clean_html_text(text: str) -> str:
    text = (text or "").replace("<p>", " ").replace("</p>", " ")
    text = text.replace("<i>", " ").replace("</i>", " ")
    text = text.replace("<pre><code>", " ").replace("</code></pre>", " ")
    text = text.replace("&quot;", '"').replace("&#x27;", "'").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    return " ".join(text.split())


def save_records(records: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def fetch_hn_hits(query: str, pages: int, hits_per_page: int, pause: float) -> list[dict]:
    rows: list[dict] = []

    for page in range(pages):
        params = {
            "query": query,
            "hitsPerPage": hits_per_page,
            "page": page,
        }
        response = requests.get(HN_SEARCH_BY_DATE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        for hit in data.get("hits", []):
            text = clean_html_text(hit.get("comment_text") or hit.get("story_text") or hit.get("title") or "")
            if not text:
                continue
            object_id = hit.get("objectID", "")
            story_id = hit.get("story_id") or object_id
            rows.append(
                {
                    "source": "hackernews",
                    "query": query,
                    "record_id": object_id,
                    "story_id": story_id,
                    "parent_id": hit.get("parent_id", ""),
                    "author": hit.get("author", ""),
                    "created_at": hit.get("created_at", ""),
                    "title": hit.get("title") or hit.get("story_title") or "",
                    "url": hit.get("url") or hit.get("story_url") or "",
                    "points": hit.get("points"),
                    "num_comments": hit.get("num_comments"),
                    "text": text,
                }
            )

        if pause:
            time.sleep(pause)

    return rows


def deduplicate_records(records: list[dict], target_total: int) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []

    for record in records:
        record_id = record.get("record_id", "")
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        deduped.append(record)
        if len(deduped) >= target_total:
            break

    return deduped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Hacker News discussions for extra sentiment comparison.")
    parser.add_argument("--queries", type=Path, default=Path("config/hackernews_queries.txt"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/hackernews_discussions.json"))
    parser.add_argument("--target-total", type=int, default=3000)
    parser.add_argument("--pages-per-query", type=int, default=5)
    parser.add_argument("--hits-per-page", type=int, default=100)
    parser.add_argument("--request-pause", type=float, default=0.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queries = load_queries(args.queries)
    if not queries:
        raise SystemExit(f"No queries found in {args.queries}.")

    records: list[dict] = []
    for query in queries:
        print(f"Collecting Hacker News records for: {query}")
        records.extend(fetch_hn_hits(query, args.pages_per_query, args.hits_per_page, args.request_pause))

    records = deduplicate_records(records, args.target_total)
    save_records(records, args.output)
    print(f"Saved {len(records):,} Hacker News records to {args.output}")


if __name__ == "__main__":
    main()
