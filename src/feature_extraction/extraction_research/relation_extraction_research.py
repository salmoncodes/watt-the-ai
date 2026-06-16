"""
relation_extraction_research.py

Performs relation extraction on academic research documents.

Input:
    data/preprocessing/clean_research_sources.json

Output:
    data/feature_extraction/research_relation_results.json
"""

from pathlib import Path
from utils.load_data import load_json
from utils.save_data import save_json
from models.rebel_model import analyze_relations

PROCESSED_DATA_DIR = Path("data/preprocessing")
OUTPUT_DIR = Path("data/feature_extraction")
INPUT_FILE = PROCESSED_DATA_DIR / "clean_research_sources.json"
OUTPUT_FILE = OUTPUT_DIR / "research_relation_results.json"

def run_relation_extraction_research():
    records = load_json(INPUT_FILE)
    results = []
    for record in records:
        text = record.get("text_clean", "")
        if not text:
            continue
        relations = analyze_relations(text)
        results.append({
            "source": "research",
            "record_id": record.get("record_id", ""),
            "doi": record.get("doi", ""),
            "title": record.get("title", ""),
            "text_clean": text,
            "relation_count": relations["relation_count"],
            "relations": relations["relations"]
        })
    save_json(OUTPUT_FILE, results)
    print(f"Extracted relations from {len(results):,} research records")

if __name__ == "__main__":
    run_relation_extraction_research()
