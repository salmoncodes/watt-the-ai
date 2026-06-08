"""
Lightweight keyword extraction wrapper.

The scaffold uses the KeyBERT model name, but this runnable project pipeline
uses TF-IDF so it can run without downloading transformer dependencies.
"""

import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer


CUSTOM_STOP_WORDS = {
    "ai",
    "artificial",
    "intelligence",
    "youtube",
    "video",
    "comment",
    "comments",
}


def _clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def extract_keywords(text, top_n=10):
    text = _clean_text(text)
    if not text:
        return []

    vectorizer = TfidfVectorizer(
        stop_words=list(ENGLISH_STOP_WORDS.union(CUSTOM_STOP_WORDS)),
        ngram_range=(1, 2),
        max_features=500,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9_\-]{2,}\b",
    )
    try:
        matrix = vectorizer.fit_transform([text])
    except ValueError:
        return []

    terms = vectorizer.get_feature_names_out()
    scores = matrix.toarray()[0]
    ranked = sorted(zip(terms, scores), key=lambda item: item[1], reverse=True)
    return [
        {
            "keyword": keyword,
            "score": float(score),
        }
        for keyword, score in ranked[:top_n]
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
