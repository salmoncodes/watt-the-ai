"""
run_all.py

Master execution script for the preprocessing pipeline.

This file runs all preprocessing modules in sequence:
1. Comments pipeline (sentiment analysis data)
2. Transcripts pipeline (RAG + topic modeling data)
3. Metadata pipeline (retrieval + context data)

This ensures that all raw YouTube data is transformed
into clean, structured datasets ready for:
- sentiment analysis
- topic modeling
- NER
- RAG indexing
"""

from comments_pipeline import preprocess_comments
from transcripts_pipeline import preprocess_transcripts
from metadata_pipeline import preprocess_metadata


def main():

    print("======================================")
    print("Starting YouTube NLP Preprocessing")
    print("======================================\n")

    print("[1/3] Processing comments...")
    preprocess_comments()
    print("Comments complete.\n")

    print("[2/3] Processing transcripts...")
    preprocess_transcripts()
    print("Transcripts complete.\n")

    print("[3/3] Processing metadata...")
    preprocess_metadata()
    print("Metadata complete.\n")

    print("======================================")
    print("All preprocessing completed successfully")
    print("======================================")


if __name__ == "__main__":
    main()
