"""
bertopic_model.py

Wrapper around the BERTopic topic modeling framework.

This module is responsible for:
- Loading and managing BERTopic model
- Extracting topics from text data
- Returning structured topic assignments

Used by:
    topic_modeling.py
"""

from bertopic import BERTopic

model = BERTopic()


def fit_model(texts):
    topics, probs = model.fit_transform(texts)
    return topics, probs


def transform_texts(texts):
    topics, probs = model.transform(texts)
    return topics, probs


def get_topic_info():
    info = model.get_topic_info()
    return info.to_dict(orient="records")


def get_topic_words(topic_id, top_n=10):
    words = model.get_topic(topic_id)
    if not words:
        return []
    return [
        {"word": w, "score": float(s)}
        for w, s in words[:top_n]
    ]


def analyze_batch(texts):
    topics, probs = transform_texts(texts)
    results = []
    for i in range(len(texts)):
        results.append({
            "text_id": i,
            "topic": int(topics[i]) if topics[i] is not None else -1,
            "probability": float(probs[i]) if probs is not None else 0.0
        })
    return results


def analyze_text(text):
    topic, prob = transform_texts([text])
    return {
        "topic": int(topic[0]) if topic[0] is not None else -1,
        "probability": float(prob[0]) if prob is not None else 0.0
    }
