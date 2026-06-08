"""
Lightweight topic modeling wrapper.

This uses TF-IDF + MiniBatchKMeans as a runnable fallback for the project
feature-extraction layer. It produces topic IDs without requiring BERTopic
transformer downloads.
"""

from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer


def analyze_batch(texts):
    cleaned = [(text or "").strip() for text in texts]
    if not cleaned:
        return []

    non_empty_count = sum(1 for text in cleaned if text)
    if non_empty_count == 0:
        return [{"text_id": i, "topic": -1, "probability": 0.0} for i in range(len(cleaned))]

    vectorizer = TfidfVectorizer(
        stop_words=list(ENGLISH_STOP_WORDS),
        max_features=5000,
        min_df=1,
        ngram_range=(1, 2),
    )
    matrix = vectorizer.fit_transform(cleaned)

    if matrix.shape[0] < 2:
        labels = [0] * matrix.shape[0]
    else:
        n_clusters = min(8, max(2, matrix.shape[0] // 3))
        model = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(matrix)

    return [
        {
            "text_id": i,
            "topic": int(labels[i]),
            "probability": 1.0,
        }
        for i in range(len(cleaned))
    ]


def analyze_text(text):
    return analyze_batch([text])[0]
