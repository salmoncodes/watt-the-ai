"""                                     
research_pipeline.py

Preprocesses trusted research-source records for RAG grounding.

Input:
    data/raw/research_sources.json

Output:
    data/preprocessing/clean_research_sources.json
"""

from pathlib import Path
from text_utils import *


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/preprocessing")

INPUT_FILE = RAW_DATA_DIR / "research_sources.json"
OUTPUT_FILE = PROCESSED_DATA_DIR / "clean_research_sources.json"


def clean_research_text(text):
    text = normalize_unicode(text)
    text = remove_noise(text)
    text = normalize_slang(text)
    text = normalize_text(text)
    text = remove_punctuation(text)
    return text


def preprocess_research_sources():
    if not INPUT_FILE.exists():
        print(f"Skipping research preprocessing; missing {INPUT_FILE}")
        return

    records = load_json(INPUT_FILE)
    processed = []

    for record in records:
        abstract = record.get("text_for_rag") or record.get("abstract", "")
        title = record.get("title", "")
        combined_text = f"{title}. {abstract}".strip()
        if not combined_text:
            continue

        abstract_clean = clean_research_text(abstract) if abstract else ""
        text_clean = clean_research_text(combined_text)
        text_topic = remove_emoji_analysis_noise(text_clean)

        if is_spam(text_clean):
            continue

        processed.append({
            "source": record.get("source", ""),
            "query": record.get("query", ""),
            "record_id": record.get("record_id", ""),
            "doi": record.get("doi", ""),
            "title": title,
            "title_clean": clean_research_text(title) if title else "",
            "abstract": record.get("abstract", ""),
            "text_original": combined_text,
            "text_clean": text_clean,
            "text_topic": text_topic,
            "text_for_rag": abstract_clean or text_clean,
            "authors": record.get("authors", []),
            "published_at": record.get("published_at", ""),
            "updated_at": record.get("updated_at", ""),
            "url": record.get("url", ""),
            "venue": record.get("venue", ""),
        })

    processed = deduplicate(processed, ["record_id", "doi", "title"])
    save_json(OUTPUT_FILE, processed)
    print(f"Processed {len(processed):,} research source records")


if __name__ == "__main__":
    preprocess_research_sources()
