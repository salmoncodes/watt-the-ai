"""
config.py

Constants for the watt-the-ai drift detection package: thresholds, limits,
schema-discovery hints, and the fixed retrieval test set. No logic lives
here -- just simple, explainable named values.
"""

import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DRIFT_EXPERIMENT_NAME = "watt-the-ai-drift"

DEFAULT_BASELINE_PATH = ROOT / "mlflow_baselines" / "baseline_stats.json"

# ----------------------------------------------------------------------
# Thresholds (kept as simple named constants so they're easy to explain)
# ----------------------------------------------------------------------
DATABASE_COUNT_PERCENT_THRESHOLD = 30.0
SENTIMENT_DRIFT_THRESHOLD = 0.20
TOPIC_DRIFT_THRESHOLD = 0.30
KEYWORD_JACCARD_THRESHOLD = 0.50
RETRIEVAL_ZERO_SOURCE_THRESHOLD = 0.30
RETRIEVAL_SOURCE_DROP_PERCENT_THRESHOLD = 40.0
RETRIEVAL_LATENCY_INCREASE_PERCENT_THRESHOLD = 50.0

TOP_TOPIC_LIMIT = 20
TOP_KEYWORD_LIMIT = 50
FALLBACK_TEXT_ROW_LIMIT = 5000

# ----------------------------------------------------------------------
# Schema discovery hints (all dynamic -- these are just candidate lists)
# ----------------------------------------------------------------------
SENTIMENT_PREFERRED_TABLES = ["sentiment_results"]
SENTIMENT_COLUMN_CANDIDATES = [
    "sentiment", "sentiment_label", "label", "polarity",
    "predicted_sentiment", "classification",
]

TOPIC_NAME_SUBSTRINGS = ["topic", "topics", "topic_model", "topic_by_sentiment"]
TOPIC_NAME_EXCLUDE_SUBSTRINGS = ["word", "representative", "by_sentiment", "tbs"]
TOPIC_COLUMN_CANDIDATES = [
    "topic", "topic_label", "topic_name", "cluster", "cluster_id", "topic_id",
]

KEYWORD_NAME_SUBSTRINGS = ["keyword", "keywords", "keyphrase", "keyphrases"]
KEYWORD_COLUMN_CANDIDATES = ["keyword", "keyphrase", "term", "word", "phrase"]

FALLBACK_TEXT_TABLES = ["comments", "hackernews", "research_sources"]
FALLBACK_TEXT_COLUMN_CANDIDATES = [
    "text", "comment_text", "cleaned_text", "content", "body", "title",
    "abstract", "text_clean", "text_original",
]

STOPWORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "was",
    "were", "has", "have", "had", "this", "that", "these", "those", "with",
    "from", "they", "them", "their", "what", "which", "who", "whom", "how",
    "why", "when", "where", "will", "would", "could", "should", "there",
    "here", "about", "into", "over", "under", "than", "then", "also",
    "just", "like", "your", "our", "his", "her", "its", "out", "off",
    "onto", "any", "some", "more", "most", "such", "only", "own", "same",
    "too", "very", "one", "two", "get", "got", "does", "did", "doing",
    "being", "been", "because", "while", "each", "few", "many", "much",
    "video", "youtube", "comment", "https", "http", "www", "com",
}

PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)

# Small, fixed evaluation set used to probe retrieval behavior for drift.
TEST_QUERIES = [
    "What do people say about data center water use?",
    "Summarize research on AI energy consumption.",
    "What is Hacker News discussing about data centers?",
    "What are common concerns about AI infrastructure?",
    "What topics appear in negative comments?",
]
RETRIEVAL_STRATEGY = "hybrid"
RETRIEVAL_TOP_K = 5
