"""
chunking.py
Turns the cleaned source JSON into embeddable "document" units, one stream per
data source, matching the three vector_db tables:
    youtube_documents | hackernews_documents | research_documents

Output is written as JSONL (one document per line) for transfer_to_vector.py to
read and embed. Embeddings are NOT produced here -- chunking only prepares text.

Document id convention:  {source}:{record}:{chunk}
"""

import sys
import argparse
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database.utils.io_utils import load_json, save_jsonl, ensure_dir


def chunk_text(text, chunk_size=200, overlap=40):
    """Split text into ~chunk_size-word chunks with a sliding overlap.

    Short text returns a single chunk; empty/whitespace text returns [].
    """
    if not text or not text.strip():
        return []
    words = text.split()
    if len(words) <= chunk_size:
        return [" ".join(words)]

    step = max(1, chunk_size - overlap)
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + chunk_size]))
        if start + chunk_size >= len(words):
            break
    return chunks


# ---------------------------------------------------------------- YOUTUBE
def chunk_youtube(videos_path, comments_path, transcripts_path, chunk_size, overlap):
    docs = []

    # video_summary: the creator's own title + description (one per video)
    for v in load_json(videos_path):
        vid = v.get("video_id")
        title = v.get("title_clean") or v.get("title_original") or ""
        desc = v.get("description_clean") or ""
        text = f"{title}. {desc}".strip()
        if not text.strip("."):
            continue
        docs.append({
            "document_id": f"yt:{vid}:summary",
            "video_id": vid,
            "doc_type": "video_summary",
            "text": text,
            "metadata": {
                "channel_title": v.get("channel_title"),
                "published_at": v.get("published_at"),
                "view_count": v.get("view_count"),
                "like_count": v.get("like_count"),
            },
        })

    # transcript_chunk: long transcript text split into chunks
    for t in load_json(transcripts_path):
        vid = t.get("video_id")
        text = t.get("text_clean") or t.get("text_original") or ""
        chunks = chunk_text(text, chunk_size, overlap)
        for i, ch in enumerate(chunks):
            docs.append({
                "document_id": f"yt:{vid}:tc_{i:04d}",
                "video_id": vid,
                "doc_type": "transcript_chunk",
                "text": ch,
                "metadata": {
                    "status": t.get("status"),
                    "chunk_index": i,
                    "num_chunks": len(chunks),
                },
            })

    # comment: one document per comment (chunked only if unusually long)
    for c in load_json(comments_path):
        vid = c.get("video_id")
        cid = c.get("comment_id")
        text = c.get("text_clean") or c.get("text_original") or ""
        chunks = chunk_text(text, chunk_size, overlap)
        for i, ch in enumerate(chunks):
            suffix = "" if len(chunks) == 1 else f"_{i}"
            docs.append({
                "document_id": f"yt:{vid}:cm_{cid}{suffix}",
                "video_id": vid,
                "doc_type": "comment",
                "text": ch,
                "metadata": {
                    "comment_id": cid,
                    "parent_id": c.get("parent_id"),
                    "author": c.get("author_display_name"),
                    "like_count": c.get("like_count"),
                    "published_at": c.get("published_at"),
                    "comment_type": c.get("comment_type"),
                    "chunk_index": i,
                    "num_chunks": len(chunks),
                },
            })

    return docs


# ------------------------------------------------------------- HACKERNEWS
def chunk_hackernews(path, chunk_size, overlap):
    docs = []
    for r in load_json(path):
        rid = r.get("record_id")
        body = r.get("text_clean") or r.get("text_original") or ""
        text = body if body.strip() else (r.get("title") or "")
        chunks = chunk_text(text, chunk_size, overlap)
        for i, ch in enumerate(chunks):
            docs.append({
                "document_id": f"hn:{rid}:{i:04d}",
                "record_id": rid,
                "story_id": r.get("story_id"),
                "doc_type": "post" if len(chunks) == 1 else "text_chunk",
                "text": ch,
                "metadata": {
                    "title": r.get("title"),
                    "author": r.get("author"),
                    "url": r.get("url"),
                    "points": r.get("points"),
                    "num_comments": r.get("num_comments"),
                    "created_at": r.get("created_at"),
                    "query": r.get("query"),
                    "chunk_index": i,
                    "num_chunks": len(chunks),
                },
            })
    return docs


# --------------------------------------------------------------- RESEARCH
def chunk_research(path, chunk_size, overlap):
    docs = []
    for record_index, r in enumerate(load_json(path)):
        rid = r.get("record_id")
        # prefer the RAG-ready text, then cleaned abstract/text
        text = r.get("text_for_rag") or r.get("text_clean") or r.get("abstract") or ""
        chunks = chunk_text(text, chunk_size, overlap)
        for i, ch in enumerate(chunks):
            docs.append({
                "document_id": f"rs:{record_index:04d}:abs_{i:04d}",
                "record_id": rid,
                "doi": r.get("doi"),
                "doc_type": "abstract_chunk",
                "text": ch,
                "metadata": {
                    "title": r.get("title"),
                    "venue": r.get("venue"),
                    "published_at": r.get("published_at"),
                    "source": r.get("source"),
                    "query": r.get("query"),
                    "chunk_index": i,
                    "num_chunks": len(chunks),
                },
            })
    return docs


def main():
    parser = argparse.ArgumentParser(
        description="Chunk cleaned sources into embeddable documents for the vector DB.")
    parser.add_argument("--input-dir", default="data")
    parser.add_argument("--output-dir", default="src/database/vector_db/chunks")
    parser.add_argument("--chunk-size", type=int, default=200, help="words per chunk")
    parser.add_argument("--overlap", type=int, default=40, help="word overlap between chunks")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    ensure_dir(out_dir)

    youtube = chunk_youtube(
        in_dir / "clean_videos.json",
        in_dir / "clean_comments.json",
        in_dir / "clean_transcripts.json",
        args.chunk_size, args.overlap)
    hackernews = chunk_hackernews(in_dir / "clean_hackernews.json", args.chunk_size, args.overlap)
    research = chunk_research(in_dir / "clean_research_sources.json", args.chunk_size, args.overlap)

    save_jsonl(out_dir / "youtube_documents.jsonl", youtube)
    save_jsonl(out_dir / "hackernews_documents.jsonl", hackernews)
    save_jsonl(out_dir / "research_documents.jsonl", research)

    print(f"YouTube documents:    {len(youtube)}")
    print(f"HackerNews documents: {len(hackernews)}")
    print(f"Research documents:   {len(research)}")
    print(f"Saved to {out_dir}")


if __name__ == "__main__":
    main()
