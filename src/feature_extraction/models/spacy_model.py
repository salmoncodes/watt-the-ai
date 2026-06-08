"""
spacy_model.py

Wrapper around the spaCy Named Entity Recognition model.

This module is responsible for:
- Loading the spaCy model
- Extracting named entities
- Returning structured entity information

Used by:
    ner_extraction.py
"""

import spacy
nlp = spacy.load("en_core_web_sm")


def extract_entities(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_
        })
    return entities


def extract_entity_count(text):
    return len(extract_entities(text))


def analyze_text(text):
    entities = extract_entities(text)
    return {
        "entity_count": len(entities),
        "entities": entities
    }


def analyze_batch(texts):
    results = []
    for text in texts:
        results.append(analyze_text(text))
    return results
