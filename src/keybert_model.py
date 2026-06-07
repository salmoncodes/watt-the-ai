"""
keybert_model.py

Wrapper around the KeyBERT keyword extraction model.

This module is responsible for:
- Loading the KeyBERT model
- Extracting keywords and keyphrases
- Returning structured keyword information

Used by:
    keyword_extraction.py
"""

from keybert import KeyBERT

model = KeyBERT()


def extract_keywords(text, top_n=10):
    keywords = model.extract_keywords(
        text,
        top_n=top_n,
        stop_words="english"
    )
    return [
        {
            "keyword": k,
            "score": float(s)
        }
        for k, s in keywords
    ]


def extract_keyword_list(text, top_n=10):
    return [k for k, _ in model.extract_keywords(text, top_n=top_n, stop_words="english")]


def analyze_text(text, top_n=10):
    keywords = extract_keywords(text, top_n)
    return {
        "keyword_count": len(keywords),
        "keywords": keywords
    }


def analyze_batch(texts, top_n=10):
    results = []
    for text in texts:
        results.append(analyze_text(text, top_n))
    return results
