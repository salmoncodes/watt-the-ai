"""
helpers.py

Small, reusable, backend-agnostic helper functions shared across the UI
modules: answer cleaning, text truncation/formatting, and simple env
checks. No Streamlit widgets and no backend imports live here -- these are
plain functions over plain data.
"""

import os

RAW_PROMPT_MARKERS = [
    # Exact, distinctive phrases lifted verbatim from every prompt template in
    # rag/prompting/templates/*.txt (qa, summarize, sentiment_insight all
    # share this framing sentence + instruction). Deliberately NOT using
    # generic fragments like "provided context" or "context:" alone -- real
    # LLM answers routinely say things like "Based on the provided context,
    # it appears that..." as normal, valid prose, and a generic fragment
    # match was incorrectly discarding those genuine answers.
    "grounded strictly in the provided context",
    "cite supporting context with its",
    # Backend fallback text (agentic_orchestration.graph.generate_answer)
    # emitted when call_llm() fails at request time even though env config
    # looked available -- still needs its own distinct message downstream.
    "llm endpoint is not configured",
]

NO_SOURCES_MESSAGE = (
    "No relevant sources were retrieved for this question. Try a broader query, "
    "change the retrieval strategy, or confirm the vector database is populated."
)

# Three visually and textually DISTINCT messages -- one per mode. These must
# never collapse into the same string, which was the original bug.
RETRIEVAL_ONLY_MESSAGE = (
    "Retrieval-only mode is active. I found relevant sources below."
)

LLM_UNAVAILABLE_MESSAGE = (
    "LLM mode was requested, but the LLM endpoint/config is not available. "
    "I used retrieval-only mode and found relevant sources below."
)

LLM_NO_ANSWER_MESSAGE = (
    "The LLM did not generate a final answer. I found relevant sources below "
    "so you can still inspect the retrieved evidence."
)

MODE_RETRIEVAL_ONLY = "retrieval_only"
MODE_LLM_UNAVAILABLE = "llm_unavailable"
MODE_LLM = "llm"

MODE_LABELS = {
    MODE_RETRIEVAL_ONLY: "Retrieval-only",
    MODE_LLM_UNAVAILABLE: "LLM unavailable \u2192 retrieval-only",
    MODE_LLM: "LLM",
}


def is_raw_prompt_or_context_dump(text):
    """True if `text` looks like a leaked prompt/context dump rather than an answer."""
    if not text:
        return False
    lowered = text.lower()
    return any(marker in lowered for marker in RAW_PROMPT_MARKERS)


def compute_llm_mode(requested_use_llm, llm_status):
    """Decide the run mode (and why) from the checkbox + real LLM availability.

    Returns (mode, mode_label, mode_reason). `mode` is one of
    MODE_RETRIEVAL_ONLY / MODE_LLM_UNAVAILABLE / MODE_LLM -- three distinct,
    non-overlapping outcomes so the UI can never render two different real
    situations with identical text.
    """
    llm_available = llm_status["available"]

    if not requested_use_llm:
        mode = MODE_RETRIEVAL_ONLY
        mode_reason = "User disabled LLM generation."
    elif requested_use_llm and not llm_available:
        mode = MODE_LLM_UNAVAILABLE
        mode_reason = llm_status["reason"]
    else:
        mode = MODE_LLM
        mode_reason = "LLM generation enabled."

    return mode, MODE_LABELS[mode], mode_reason


def clean_assistant_answer(answer, source_count, mode):
    """Never show a raw prompt/context dump (or an empty answer) as the visible answer.

    `mode` (one of MODE_RETRIEVAL_ONLY / MODE_LLM_UNAVAILABLE / MODE_LLM) must
    be the resolved mode from compute_llm_mode() -- NOT just the raw checkbox
    value -- so "deliberately off", "checked but unavailable", and a real LLM
    answer are always three distinct visible outcomes.
    """
    if source_count == 0:
        return NO_SOURCES_MESSAGE
    if mode == MODE_RETRIEVAL_ONLY:
        return RETRIEVAL_ONLY_MESSAGE
    if mode == MODE_LLM_UNAVAILABLE:
        return LLM_UNAVAILABLE_MESSAGE
    if not answer or is_raw_prompt_or_context_dump(answer):
        return LLM_NO_ANSWER_MESSAGE
    return answer


def safe_truncate(text, max_chars=400):
    """Truncate `text` to `max_chars`, adding an ellipsis if it was cut."""
    text = str(text or "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def format_seconds(seconds):
    """Format a latency value as e.g. '2.31s', or 'n/a' if missing/invalid."""
    if seconds is None:
        return "n/a"
    try:
        return f"{float(seconds):.2f}s"
    except (TypeError, ValueError):
        return "n/a"


def get_strategy_override(strategy):
    """Translate the sidebar's 'auto' option into the None run_agent() expects."""
    return None if strategy == "auto" else strategy


def count_vector_documents(db_status):
    """Per-source + total vector document counts from a collect_database_status() dict."""
    tables = ((db_status or {}).get("vector_db") or {}).get("tables") or {}
    counts = {
        "youtube_documents": tables.get("youtube_documents") or 0,
        "hackernews_documents": tables.get("hackernews_documents") or 0,
        "research_documents": tables.get("research_documents") or 0,
    }
    counts["total"] = sum(v for v in counts.values() if isinstance(v, int))
    return counts


def check_llm_env():
    """Whether the big LLM endpoint is configured, per agentic_orchestration.llm_client.call_llm.

    call_llm() only hard-requires RAG_BIG_LLM_BASE_URL (it returns "" and skips
    the request entirely if that's missing); RAG_BIG_LLM_MODEL is optional and
    falls back to "local-model" if unset. So availability must be judged on
    the base URL alone -- requiring the model too would report "unavailable"
    for a setup that would actually work.

    Returns {"available": bool, "missing": [...], "reason": str}.
    """
    base_url = os.getenv("RAG_BIG_LLM_BASE_URL")
    missing = [] if base_url else ["RAG_BIG_LLM_BASE_URL"]
    available = not missing

    if available:
        reason = "RAG_BIG_LLM_BASE_URL is configured."
    else:
        reason = (
            "RAG_BIG_LLM_BASE_URL is not set, so agentic_orchestration.llm_client.call_llm() "
            "returns no answer and the backend falls back to retrieval-only behavior."
        )

    return {"available": available, "missing": missing, "reason": reason}
