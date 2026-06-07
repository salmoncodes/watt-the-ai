"""
vader_model.py

Wrapper around the VADER sentiment analysis model.

This module is responsible for:
- Loading the VADER analyzer
- Calculating sentiment scores
- Assigning sentiment labels

Used by:
    sentiment_analysis.py
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()


def get_sentiment_label(compound_score):
    if compound_score >= 0.05:
        return "positive"
    if compound_score <= -0.05:
        return "negative"
    return "neutral"


def analyze_sentiment(text):
    scores = analyzer.polarity_scores(text)
    return {
        "negative": scores["neg"],
        "neutral": scores["neu"],
        "positive": scores["pos"],
        "compound": scores["compound"],
        "label": get_sentiment_label(scores["compound"])
    }


def analyze_batch(texts):
    results = []
    for text in texts:
        results.append(analyze_sentiment(text))
    return results
