"""
BERTopic topic modeling wrapper.

This module fits BERTopic on the provided batch and returns topic assignments,
probabilities, and top topic words.
"""

from bertopic import BERTopic
from sklearn.cluster import KMeans


def analyze_batch(texts):
    cleaned = [(text or "").strip() for text in texts]
    if not cleaned:
        return []

    if len(cleaned) < 5:
        return [
            {
                "text_id": i,
                "topic": 0 if text else -1,
                "probability": 1.0 if text else 0.0,
                "topic_words": [],
            }
            for i, text in enumerate(cleaned)
        ]

    cluster_model = KMeans(n_clusters=min(8, max(2, len(cleaned) // 3)), random_state=42, n_init=10)
    model = BERTopic(hdbscan_model=cluster_model, calculate_probabilities=False, verbose=False)
    topics, probs = model.fit_transform(cleaned)

    results = []
    for i, topic_id in enumerate(topics):
        topic_words = model.get_topic(topic_id) or []
        probability = 0.0
        if probs is not None and len(probs) > i:
            row = probs[i]
            if topic_id >= 0 and len(row) > topic_id:
                probability = float(row[topic_id])
            elif len(row):
                probability = float(max(row))
        elif topic_id >= 0:
            probability = 1.0

        results.append(
            {
                "text_id": i,
                "topic": int(topic_id) if topic_id is not None else -1,
                "probability": probability,
                "topic_words": [
                    {"word": word, "score": float(score)}
                    for word, score in topic_words[:10]
                ],
            }
        )

    return results


def analyze_text(text):
    return analyze_batch([text])[0]
