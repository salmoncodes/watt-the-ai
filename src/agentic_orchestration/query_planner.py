import json
import re
from pathlib import Path

from agentic_orchestration.llm_client import call_small_llm, parse_json


ROOT = Path(__file__).resolve().parents[2]
ROUTER_PROMPT = ROOT / "config" / "rag_router_prompt.txt"


def has_word(text, word):
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def fallback_plan(query):
    q = query.lower()
    source = ""
    sentiment = ""
    relation = ""
    keyword = ""

    if has_word(q, "hacker") or has_word(q, "hn"):
        source = "hackernews"
    elif any(has_word(q, word) for word in ["paper", "research", "study", "evidence"]):
        source = "research"
    elif any(has_word(q, word) for word in ["youtube", "comment", "comments", "viewer", "viewers", "people"]):
        source = "youtube"

    for label in ["positive", "negative", "neutral"]:
        if has_word(q, label):
            sentiment = label

    if any(has_word(q, word) for word in ["relation", "relations", "cause", "use", "need", "connect", "connection"]):
        for word in ["cause", "use", "need", "water", "energy", "data center"]:
            if has_word(q, word):
                relation = word
                break

    for word in ["water", "energy", "electricity", "data center", "datacenter", "emissions", "carbon"]:
        if has_word(q, word):
            keyword = word
            break

    return {
        "rewritten_query": query,
        "source": source,
        "sentiment": sentiment,
        "relation_contains": relation,
        "keyword": keyword,
        "task": "sentiment_insight" if sentiment or "sentiment" in q else "qa",
    }


def plan_query(query):
    if not ROUTER_PROMPT.exists():
        return fallback_plan(query)

    router_prompt = ROUTER_PROMPT.read_text(encoding="utf-8")
    output = call_small_llm(router_prompt + "\n\nUser question:\n" + query)
    data = parse_json(output)
    if not data:
        return fallback_plan(query)

    source_map = {
        "comment": "youtube",
        "video": "youtube",
        "transcript": "youtube",
        "topic_by_sentiment": "youtube",
        "hackernews": "hackernews",
        "trusted_research": "research",
    }
    sentiment = data.get("sentiment_label") or ""
    fallback = fallback_plan(query)
    return {
        "rewritten_query": data.get("rewritten_query") or query,
        "source": source_map.get(data.get("source_type"), ""),
        "sentiment": sentiment,
        "relation_contains": data.get("relation_contains") or "",
        "keyword": data.get("keyword") or fallback.get("keyword", ""),
        "task": "sentiment_insight" if sentiment else "qa",
        "router_raw": json.dumps(data, ensure_ascii=False),
    }
