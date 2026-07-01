"""
sources.py

Extraction and rendering of retrieved source documents, plus the
"retrieved context" debug view built from those same documents. Never
assumes a particular metadata shape.
"""

import html

import streamlit as st

from ui.helpers import safe_truncate

SOURCE_METADATA_KEYS = [
    "video_id", "comment_id", "published_at", "like_count",
    "title", "url", "doi", "venue", "points", "num_comments",
]


def serialize_source_document(doc):
    """Convert a source document (dict, or a retriever's dataclass/object) into a plain dict."""
    if isinstance(doc, dict):
        return {
            "document_id": doc.get("document_id"),
            "text": doc.get("text", ""),
            "score": doc.get("score"),
            "source": doc.get("source"),
            "strategy": doc.get("strategy"),
            "doc_type": doc.get("doc_type"),
            "metadata": doc.get("metadata", {}) or {},
        }
    return {
        "document_id": getattr(doc, "document_id", None),
        "text": getattr(doc, "text", ""),
        "score": getattr(doc, "score", None),
        "source": getattr(doc, "source", None),
        "strategy": getattr(doc, "strategy", None),
        "doc_type": getattr(doc, "doc_type", None),
        "metadata": getattr(doc, "metadata", {}) or {},
    }


def extract_source_documents(result):
    """Prefer result['source_documents']; fall back to serialized result['docs'].
    Never relies on result['sources'] alone (those may only be document IDs)."""
    result = result or {}

    source_documents = result.get("source_documents")
    if isinstance(source_documents, list):
        return source_documents

    docs = result.get("docs")
    if isinstance(docs, list):
        return [serialize_source_document(d) for d in docs]

    return []


def render_sources(source_documents):
    """Render each source as a compact card: label, score, truncated snippet, metadata."""
    if not source_documents:
        st.caption("No sources were retrieved for this answer.")
        return

    for i, doc in enumerate(source_documents, 1):
        doc = doc or {}
        metadata = doc.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        snippet = safe_truncate(doc.get("text") or "", 400)

        try:
            score_text = f"{float(doc.get('score')):.3f}"
        except (TypeError, ValueError):
            score_text = "n/a"

        meta_lines = []
        for key in SOURCE_METADATA_KEYS:
            value = metadata.get(key)
            if value not in (None, ""):
                meta_lines.append(
                    f"<div><span class='muted-label'>{html.escape(key)}:</span> "
                    f"{html.escape(str(value))}</div>"
                )

        url = metadata.get("url")
        link_html = ""
        if url:
            safe_url = html.escape(str(url))
            link_html = f'<div><a href="{safe_url}" target="_blank" style="color:#A5B4FC;">Open source</a></div>'

        source_label = html.escape(str(doc.get("source") or "unknown"))
        doc_type_label = html.escape(str(doc.get("doc_type") or "n/a"))
        doc_id_label = html.escape(str(doc.get("document_id") or "n/a"))

        st.markdown(
            f"""
            <div class="source-card">
                <div style="font-weight:700; color:#F9FAFB; margin-bottom:6px;">
                    [{i}] {source_label} &middot; {doc_type_label}
                </div>
                <div style="color:#94A3B8; font-size:0.8rem; margin-bottom:8px;">
                    Score: {score_text} &middot; id: {doc_id_label}
                </div>
                <div style="color:#CBD5E1; line-height:1.5; margin-bottom:8px;">
                    {html.escape(snippet)}
                </div>
                {''.join(meta_lines)}
                {link_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_retrieved_context(source_documents):
    """Plain-text view of the same source documents, for the 'Show retrieved context' toggle."""
    if not source_documents:
        st.caption("No retrieved context available.")
        return

    parts = []
    for i, doc in enumerate(source_documents, 1):
        doc = doc or {}
        parts.append(
            f"[{i}] source={doc.get('source')} type={doc.get('doc_type')} id={doc.get('document_id')}\n"
            f"{doc.get('text', '')}"
        )
    st.code("\n\n".join(parts), language=None)
