"""
ner_extraction_research.py

Performs Named Entity Recognition (NER) on research papers using spaCy.
"""

from pathlib import Path

from utils.load_data import load_json
from utils.save_data import save_json
from models.spacy_model import analyze_text


PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")

INPUT_FILE = PROCESSED_DATA_DIR / "clean_research_sources.json"
OUTPUT_FILE = OUTPUT_DIR / "research_ner_results.json"


def run_ner_extraction_research():
    records = load_json(INPUT_FILE)

    results = []

    for record in records:
        text = record.get("text_clean", "")
        if not text:
            continue

        ner = analyze_text(text)

        results.append({
            "record_id": record["record_id"],
            "doi": record.get("doi", ""),
            "title": record.get("title", ""),
            "entity_count": ner["entity_count"],
            "entities": ner["entities"]
        })

    save_json(OUTPUT_FILE, results)
    print(f"Extracted entities for {len(results):,} research records")


if __name__ == "__main__":
    run_ner_extraction_research()
