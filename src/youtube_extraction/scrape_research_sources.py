import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import requests


ARXIV_API_URL = "https://export.arxiv.org/api/query"
OPENALEX_API_URL = "https://api.openalex.org/works"
CROSSREF_API_URL = "https://api.crossref.org/works"


try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    pass


def load_queries(path: Path) -> list[str]:
    queries: list[str] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        queries.append(line)
    return queries


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def save_records(records: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def request_json(url: str, params: dict, headers: dict, pause: float) -> dict:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    if pause:
        time.sleep(pause)
    return response.json()


def fetch_arxiv(query: str, max_results: int, pause: float) -> list[dict]:
    params = {
        "search_query": f'all:"{query}"',
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    response = requests.get(ARXIV_API_URL, params=params, timeout=30)
    response.raise_for_status()
    if pause:
        time.sleep(pause)

    root = ET.fromstring(response.text)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    rows: list[dict] = []

    for entry in root.findall("atom:entry", namespace):
        arxiv_id = entry.findtext("atom:id", default="", namespaces=namespace)
        title = normalize_space(entry.findtext("atom:title", default="", namespaces=namespace))
        abstract = normalize_space(entry.findtext("atom:summary", default="", namespaces=namespace))
        published_at = entry.findtext("atom:published", default="", namespaces=namespace)
        updated_at = entry.findtext("atom:updated", default="", namespaces=namespace)
        authors = [
            normalize_space(author.findtext("atom:name", default="", namespaces=namespace))
            for author in entry.findall("atom:author", namespace)
        ]
        rows.append(
            {
                "source": "arxiv",
                "query": query,
                "record_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published_at": published_at,
                "updated_at": updated_at,
                "doi": "",
                "url": arxiv_id,
                "venue": "arXiv",
                "text_for_rag": f"{title}. {abstract}".strip(),
            }
        )

    return rows


def inverted_index_to_text(index: Optional[dict]) -> str:
    if not index:
        return ""

    positioned_words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            positioned_words.append((position, word))
    positioned_words.sort(key=lambda item: item[0])
    return normalize_space(" ".join(word for _, word in positioned_words))


def fetch_openalex(
    query: str,
    max_results: int,
    openalex_api_key: Optional[str],
    mailto: Optional[str],
    pause: float,
) -> list[dict]:
    params = {
        "search": query,
        "per-page": min(max_results, 200),
        "select": "id,doi,title,display_name,publication_year,publication_date,authorships,primary_location,abstract_inverted_index",
    }
    if mailto:
        params["mailto"] = mailto
    if openalex_api_key:
        params["api_key"] = openalex_api_key

    headers = {"User-Agent": "watt-the-ai-course-project/1.0"}
    if mailto:
        headers["User-Agent"] = f"watt-the-ai-course-project/1.0 (mailto:{mailto})"

    data = request_json(OPENALEX_API_URL, params=params, headers=headers, pause=pause)
    rows: list[dict] = []

    for item in data.get("results", []):
        title = normalize_space(item.get("display_name") or item.get("title") or "")
        abstract = inverted_index_to_text(item.get("abstract_inverted_index"))
        authors = [
            author.get("author", {}).get("display_name", "")
            for author in item.get("authorships", [])
            if author.get("author", {}).get("display_name")
        ]
        location = item.get("primary_location") or {}
        source = location.get("source") or {}
        rows.append(
            {
                "source": "openalex",
                "query": query,
                "record_id": item.get("id", ""),
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published_at": item.get("publication_date", ""),
                "publication_year": item.get("publication_year", ""),
                "doi": item.get("doi", ""),
                "url": item.get("id", ""),
                "venue": source.get("display_name", ""),
                "text_for_rag": f"{title}. {abstract}".strip(),
            }
        )

    return rows


def fetch_crossref(query: str, max_results: int, mailto: Optional[str], pause: float) -> list[dict]:
    params = {
        "query": query,
        "rows": min(max_results, 100),
        "select": "DOI,title,abstract,author,published-print,published-online,container-title,URL",
    }
    if mailto:
        params["mailto"] = mailto

    headers = {"User-Agent": "watt-the-ai-course-project/1.0"}
    if mailto:
        headers["User-Agent"] = f"watt-the-ai-course-project/1.0 (mailto:{mailto})"

    data = request_json(CROSSREF_API_URL, params=params, headers=headers, pause=pause)
    rows: list[dict] = []

    for item in data.get("message", {}).get("items", []):
        title = normalize_space((item.get("title") or [""])[0])
        abstract = normalize_space(item.get("abstract", ""))
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            name = normalize_space(f"{given} {family}")
            if name:
                authors.append(name)

        date_parts = (
            item.get("published-online", {}).get("date-parts")
            or item.get("published-print", {}).get("date-parts")
            or [[]]
        )
        published_at = "-".join(str(part) for part in date_parts[0]) if date_parts[0] else ""

        rows.append(
            {
                "source": "crossref",
                "query": query,
                "record_id": item.get("DOI", ""),
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published_at": published_at,
                "doi": item.get("DOI", ""),
                "url": item.get("URL", ""),
                "venue": (item.get("container-title") or [""])[0],
                "text_for_rag": f"{title}. {abstract}".strip(),
            }
        )

    return rows


def deduplicate_records(records: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []

    for record in records:
        key = (
            record.get("doi")
            or record.get("record_id")
            or f"{record.get('source')}:{record.get('title')}"
        ).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)

    return deduped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect trusted research metadata for RAG.")
    parser.add_argument("--queries", type=Path, default=Path("config/research_queries.txt"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/research_sources.json"))
    parser.add_argument("--max-results-per-query", type=int, default=15)
    parser.add_argument("--sources", nargs="+", default=["arxiv", "openalex", "crossref"])
    parser.add_argument("--request-pause", type=float, default=1.0)
    parser.add_argument("--openalex-api-key", default=os.getenv("OPENALEX_API_KEY"))
    parser.add_argument("--mailto", default=os.getenv("RESEARCH_API_EMAIL"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queries = load_queries(args.queries)
    if not queries:
        raise SystemExit(f"No queries found in {args.queries}.")

    requested_sources = {source.lower() for source in args.sources}
    records: list[dict] = []

    for query in queries:
        print(f"Collecting research records for: {query}")
        try:
            if "arxiv" in requested_sources:
                records.extend(fetch_arxiv(query, args.max_results_per_query, args.request_pause))
        except requests.RequestException as error:
            print(f"Skipping arXiv query '{query}': {error}")

        try:
            if "openalex" in requested_sources:
                records.extend(
                    fetch_openalex(
                        query=query,
                        max_results=args.max_results_per_query,
                        openalex_api_key=args.openalex_api_key,
                        mailto=args.mailto,
                        pause=args.request_pause,
                    )
                )
        except requests.RequestException as error:
            print(f"Skipping OpenAlex query '{query}': {error}")

        try:
            if "crossref" in requested_sources:
                records.extend(fetch_crossref(query, args.max_results_per_query, args.mailto, args.request_pause))
        except requests.RequestException as error:
            print(f"Skipping Crossref query '{query}': {error}")

    records = deduplicate_records(records)
    save_records(records, args.output)
    print(f"Saved {len(records):,} research records to {args.output}")


if __name__ == "__main__":
    main()
