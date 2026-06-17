"""
run_all_feature_extraction.py

Runs the feature extraction files.

It runs YouTube, Hacker News, and research feature extraction.
"""

from extraction_youtube.sentiment_analysis import run_sentiment_analysis
from extraction_youtube.ner_extraction import run_ner_extraction
from extraction_youtube.keyword_extraction import run_keyword_extraction
from extraction_youtube.topic_modeling import run_topic_modeling
from extraction_youtube.relation_extraction import run_relation_extraction

from extraction_hackernews.sentiment_analysis_hackernews import run_sentiment_analysis_hackernews
from extraction_hackernews.ner_extraction_hackernews import run_ner_extraction_hackernews
from extraction_hackernews.keyword_extraction_hackernews import run_keyword_extraction_hackernews
from extraction_hackernews.topic_modeling_hackernews import run_topic_modeling_hackernews
from extraction_hackernews.relation_extraction_hackernews import run_relation_extraction_hackernews

from extraction_research.ner_extraction_research import run_ner_extraction_research
from extraction_research.keyword_extraction_research import run_keyword_extraction_research
from extraction_research.topic_modeling_research import run_topic_modeling_research
from extraction_research.relation_extraction_research import run_relation_extraction_research

def main():

    print("======================================")
    print("Starting Feature Extraction Pipeline for YouTube")
    print("======================================\n")

    print("[1/5] Running Sentiment Analysis for YouTube...")
    run_sentiment_analysis()
    print("Sentiment Analysis Complete.\n")

    print("[2/5] Running Named Entity Recognition for YouTube...")
    run_ner_extraction()
    print("NER Complete.\n")

    print("[3/5] Running Keyword Extraction for YouTube...")
    run_keyword_extraction()
    print("Keyword Extraction Complete.\n")

    print("[4/5] Running Topic Modeling for Youtube...")
    run_topic_modeling()
    print("Topic Modeling Complete.\n")

    print("[5/5] Running Relation Extraction for Youtube...")
    run_relation_extraction()
    print("Relation Extraction Complete.\n")

    print("======================================")
    print("Feature Extraction Pipeline for Youtube Completed")
    print("======================================")

    print("======================================")
    print("Starting Feature Extraction Pipeline for Hacker News")
    print("======================================\n")

    print("[1/5] Running Sentiment Analysis for Hacker News...")
    run_sentiment_analysis_hackernews()
    print("Sentiment Analysis Complete.\n")

    print("[2/5] Running Named Entity Recognition for Hacker News...")
    run_ner_extraction_hackernews()
    print("NER Complete.\n")

    print("[3/5] Running Keyword Extraction for Hacker News...")
    run_keyword_extraction_hackernews()
    print("Keyword Extraction Complete.\n")

    print("[4/5] Running Topic Modeling for Hacker News...")
    run_topic_modeling_hackernews()
    print("Topic Modeling Complete.\n")

    print("[5/5] Running Relation Extraction for Hacker News...")
    run_relation_extraction_hackernews()
    print("Relation Extraction Complete.\n")

    print("======================================")
    print("Feature Extraction Pipeline for Hacker News Completed")
    print("======================================")

    print("======================================")
    print("Starting Feature Extraction Pipeline for Research")
    print("======================================\n")

    print("[1/4] Running Named Entity Recognition for Research...")
    run_ner_extraction_research()
    print("NER Complete.\n")

    print("[2/4] Running Keyword Extraction for Research...")
    run_keyword_extraction_research()
    print("Keyword Extraction Complete.\n")

    print("[3/4] Running Topic Modeling for Research...")
    run_topic_modeling_research()
    print("Topic Modeling Complete.\n")

    print("[4/4] Running Relation Extraction for Research...")
    run_relation_extraction_research()
    print("Relation Extraction Complete.\n")

    print("======================================")
    print("Feature Extraction Pipeline for Research Completed")
    print("======================================")

if __name__ == "__main__":
    main()
