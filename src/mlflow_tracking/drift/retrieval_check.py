"""
retrieval_check.py

Collects a retrieval-behavior snapshot by running a small fixed set of test
queries through the RAG retriever in no-LLM / retrieval-only mode.

This module only collects data -- it does not log to MLflow and does not
compare against a baseline (see compare.py for that).
"""

import time

from mlflow_tracking.drift.config import TEST_QUERIES, RETRIEVAL_STRATEGY, RETRIEVAL_TOP_K


def collect_retrieval_snapshot():
    """Run TEST_QUERIES through the RAG retriever (no LLM) and measure latency /
    source-document counts. Never raises: import or per-query failures are
    recorded, not propagated."""
    snapshot = {
        "available": False,
        "reason": None,
        "test_query_count": len(TEST_QUERIES),
        "strategy": RETRIEVAL_STRATEGY,
        "top_k": RETRIEVAL_TOP_K,
        "average_latency_seconds": None,
        "average_source_documents": None,
        "zero_source_rate": None,
        "queries": [],
    }

    try:
        from agentic_orchestration.graph import run_agent
    except Exception as exc:
        snapshot["reason"] = f"could not import run_agent: {exc}"
        return snapshot

    latencies = []
    source_counts = []
    zero_count = 0

    for query in TEST_QUERIES:
        entry = {"query": query, "latency_seconds": None, "source_document_count": None, "error": None}
        start = time.time()
        try:
            result = run_agent(
                query, no_llm=True, top_k=RETRIEVAL_TOP_K, strategy_override=RETRIEVAL_STRATEGY
            )
            latency = time.time() - start

            source_documents = result.get("source_documents") if isinstance(result, dict) else None
            if isinstance(source_documents, list):
                count = len(source_documents)
            else:
                docs = result.get("docs") if isinstance(result, dict) else None
                if isinstance(docs, list):
                    count = len(docs)
                else:
                    sources = result.get("sources") if isinstance(result, dict) else None
                    count = len(sources) if isinstance(sources, list) else 0

            entry["latency_seconds"] = latency
            entry["source_document_count"] = count
            latencies.append(latency)
            source_counts.append(count)
            if count == 0:
                zero_count += 1
        except Exception as exc:
            entry["error"] = str(exc)
            source_counts.append(0)
            zero_count += 1
        snapshot["queries"].append(entry)

    total_queries = len(TEST_QUERIES)
    snapshot["available"] = True
    snapshot["average_latency_seconds"] = (sum(latencies) / len(latencies)) if latencies else None
    snapshot["average_source_documents"] = (
        sum(source_counts) / len(source_counts) if source_counts else 0.0
    )
    snapshot["zero_source_rate"] = (zero_count / total_queries) if total_queries else None
    return snapshot
