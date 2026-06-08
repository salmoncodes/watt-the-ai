"""
KeyBERT keyword extraction wrapper.

This module loads KeyBERT once and returns structured keyword/keyphrase output.
"""

from keybert import KeyBERT


model = KeyBERT()


def extract_keywords(text, top_n=10):
    if not text or not text.strip():
        return []

    keywords = model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=top_n,
    )
    return [
        {
            "keyword": keyword,
            "score": float(score),
        }
        for keyword, score in keywords
    ]


def extract_keyword_list(text, top_n=10):
    return [item["keyword"] for item in extract_keywords(text, top_n)]


def analyze_text(text, top_n=10):
    keywords = extract_keywords(text, top_n)
    return {
        "keyword_count": len(keywords),
        "keywords": keywords,
    }


def analyze_batch(texts, top_n=10):
    return [analyze_text(text, top_n) for text in texts]
