# Data Collection Log

Date: May 20, 2026

## Current Raw Data

- `data/raw/youtube_comments.json`: 40,000 comment records
- `data/raw/youtube_videos.json`: 50 video metadata records
- `data/raw/youtube_transcripts_sample.json`: 25 attempted transcripts, 24 successful
- `data/raw/discovered_videos.json`: initial discovered video pool
- `data/raw/discovered_videos_extra.json`: extra discovered video pool used to reach 40,000 comments

## Course-Lab Connection

The comment scraping code is based on the professor-provided `YouTube_Comments_Advanced.ipynb` lab notebook. The lab already demonstrated:

- `googleapiclient.discovery`
- `youtube.commentThreads().list(...)`
- `maxResults=100`
- pagination with `nextPageToken`
- extracting author, date, likes, text, video ID, and public status
- looping through multiple video IDs

The project version refactored that notebook logic into scripts and extended it with JSON output, config-driven video IDs, duplicate protection, reply scraping, metadata scraping, transcript attempts, progress output, and error handling.

The comment dataset contains:

- 13,593 top-level comments
- 26,407 replies
- comments from 28 videos

## Quota Clarification

The YouTube limit shown in Google Cloud is 10,000 quota units per day, not 10,000 comments.

For this project:

- `commentThreads.list` costs 1 quota unit per page and can return up to 100 top-level comments.
- `comments.list` costs 1 quota unit per page and can return up to 100 replies.
- `videos.list` for metadata is low cost and supports up to 50 IDs per request.
- `search.list` is expensive at 100 quota units per request, so it should only be used for discovery, not repeated scraping.

The 40,000-comment scrape succeeded because the API quota is based on requests/pages, not individual comments.

## Publishing Note

Before publishing:

- rotate or restrict the exposed key in Google Cloud
- keep `.env`, raw data, and credentials out of GitHub
- use `PUBLISHING_CHECKLIST.md`

## Transcript Note

Transcript collection worked for 24 of the first 25 videos, then later requests were blocked by YouTube's transcript service. This is separate from the official YouTube Data API quota. Use the available transcripts as extra RAG context and mention this limitation in the report.
