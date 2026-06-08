"""
run_all_feature_extraction.py

Master execution script for the Feature Extraction layer.

This file runs all feature extraction modules in sequence:
1. Sentiment Analysis
2. Named Entity Recognition (NER)
3. Keyword Extraction
4. Topic Modeling

This ensures that all processed data is enriched with:
- sentiment signals
- entities
- keywords
- topic assignments

Output is used for:
- RAG indexing
- analytics dashboard
- MLflow evaluation
"""

from sentiment_analysis import run_sentiment_analysis
from ner_extraction import run_ner_extraction
from keyword_extraction import run_keyword_extraction
from topic_modeling import run_topic_modeling


def main():

    print("======================================")
    print("Starting Feature Extraction Pipeline")
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
    print("Feature Extraction Pipeline Completed")
    print("======================================")


if __name__ == "__main__":
    main()
