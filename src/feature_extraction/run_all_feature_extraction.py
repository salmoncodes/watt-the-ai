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

from sentiment_analysis_hackernews import run_sentiment_analysis_hackernews
from ner_extraction_hackernews import run_ner_extraction_hackernews
from keyword_extraction_hackernews import run_keyword_extraction_hackernews
from topic_modeling_hackernews import run_topic_modeling_hackernews

from ner_extraction_research import run_ner_extraction_research
from keyword_extraction_research import run_keyword_extraction_research
from topic_modeling_research import run_topic_modeling_research


def main():

    print("======================================")
    print("Starting Feature Extraction Pipeline for YouTube")
    print("======================================\n")

    print("[1/4] Running Sentiment Analysis for YouTube...")
    run_sentiment_analysis()
    print("Sentiment Analysis Complete.\n")

    print("[2/4] Running Named Entity Recognition for YouTube...")
    run_ner_extraction()
    print("NER Complete.\n")

    print("[3/4] Running Keyword Extraction for YouTube...")
    run_keyword_extraction()
    print("Keyword Extraction Complete.\n")

    print("[4/4] Running Topic Modeling for Youtube...")
    run_topic_modeling()
    print("Topic Modeling Complete.\n")

    print("======================================")
    print("Feature Extraction Pipeline for Youtube Completed")
    print("======================================")

    print("======================================")
    print("Starting Feature Extraction Pipeline for Hacker News")
    print("======================================\n")

    print("[1/4] Running Sentiment Analysis for Hacker News...")
    run_sentiment_analysis_hackernews()
    print("Sentiment Analysis Complete.\n")

    print("[2/4] Running Named Entity Recognition for Hacker News...")
    run_ner_extraction_hackernews()
    print("NER Complete.\n")

    print("[3/4] Running Keyword Extraction for Hacker News...")
    run_keyword_extraction_hackernews()
    print("Keyword Extraction Complete.\n")

    print("[4/4] Running Topic Modeling for Hacker News...")
    run_topic_modeling_hackernews()
    print("Topic Modeling Complete.\n")

    print("======================================")
    print("Feature Extraction Pipeline for Hacker News Completed")
    print("======================================")

    print("======================================")
    print("Starting Feature Extraction Pipeline for Research")
    print("======================================\n")

    print("[1/3] Running Named Entity Recognition for Research...")
    run_ner_extraction_research()
    print("NER Complete.\n")

    print("[2/3] Running Keyword Extraction for Research...")
    run_keyword_extraction_research()
    print("Keyword Extraction Complete.\n")

    print("[3/3] Running Topic Modeling for Research...")
    run_topic_modeling_research()
    print("Topic Modeling Complete.\n")

    print("======================================")
    print("Feature Extraction Pipeline for Research Completed")
    print("======================================")

if __name__ == "__main__":
    main()
