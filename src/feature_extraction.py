"""
feature_extraction.py

Main controller for the Feature Extraction layer.

This file executes:
- Sentiment Analysis
- Named Entity Recognition
- Keyword Extraction
- Topic Modeling

Used by:
    run_all.py
"""

from sentiment_analysis import run_sentiment_analysis
from ner_extraction import run_ner_extraction
from keyword_extraction import run_keyword_extraction
from topic_modeling import run_topic_modeling


def run_feature_extraction():

    print("======================================")
    print("Starting Feature Extraction")
    print("======================================\n")

    print("[1/4] Running Sentiment Analysis...")
    run_sentiment_analysis()
    print("Sentiment Analysis Complete.\n")

    print("[2/4] Running Named Entity Recognition...")
    run_ner_extraction()
    print("NER Complete.\n")

    print("[3/4] Running Keyword Extraction...")
    run_keyword_extraction()
    print("Keyword Extraction Complete.\n")

    print("[4/4] Running Topic Modeling...")
    run_topic_modeling()
    print("Topic Modeling Complete.\n")

    print("======================================")
    print("Feature Extraction Complete")
    print("======================================")


if __name__ == "__main__":
    run_feature_extraction()
