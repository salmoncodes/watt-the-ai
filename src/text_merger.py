"""
text_merger.py

Combines text from multiple processed sources.

Used by:
    keyword_extraction.py
    topic_modeling.py

The goal is to create richer documents by
combining metadata, transcripts, and comments.
"""


def merge_video_text(video_record, transcript_record=None, comment_records=None):
    text_parts = []
    if video_record:
        title = video_record.get("title_clean", "")
        description = video_record.get("description_clean", "")
        if title:
            text_parts.append(title)
        if description:
            text_parts.append(description)
    if transcript_record:
        transcript_text = transcript_record.get("text_clean", "")
        if transcript_text:
            text_parts.append(transcript_text)
    if comment_records:
        for comment in comment_records:
            comment_text = comment.get("text_clean", "")
            if comment_text:
                text_parts.append(comment_text)
    return "\n".join(text_parts)


def build_document_map(videos, transcripts, comments):
    transcript_map = {transcript["video_id"]: transcript for transcript in transcripts}
    comment_map = {}
    for comment in comments:
        video_id = comment["video_id"]
        if video_id not in comment_map:
            comment_map[video_id] = []
        comment_map[video_id].append(comment)
    documents = []
    for video in videos:
        video_id = video["video_id"]
        merged_text = merge_video_text(video_record=video, transcript_record=transcript_map.get(video_id), comment_records=comment_map.get(video_id, []))
        documents.append({"video_id": video_id, "text": merged_text})
    return documents
