"""
chat.py

Chat message rendering and query execution. Calls the existing
run_agent()/log_rag_query() (via ui.services) without changing their
behavior or signatures.
"""

import html
import time

import streamlit as st

from ui.helpers import (
    clean_assistant_answer,
    get_strategy_override,
    check_llm_env,
    compute_llm_mode,
)
from ui.sources import extract_source_documents, render_sources, render_retrieved_context
from ui.debug import render_debug_info
from ui.services import call_run_agent, call_log_rag_query


def _format_answer_html(text):
    return html.escape(text or "").replace("\n", "<br>")


def render_user_message(content):
    st.markdown(
        f"""
        <div class="message-row user-row">
            <div class="user-bubble">{_format_answer_html(content)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_assistant_message(message, settings):
    source_documents = message.get("source_documents") or []

    meta_bits = []
    if message.get("mode_label"):
        meta_bits.append(f"Mode: {message['mode_label']}")
    if message.get("strategy"):
        meta_bits.append(f"Strategy: {message['strategy']}")
    meta_bits.append(f"Sources: {len(source_documents)}")
    if message.get("latency_seconds") is not None:
        meta_bits.append(f"{message['latency_seconds']:.2f}s")
    meta_row = " · ".join(meta_bits)

    st.markdown(
        f"""
        <div class="message-row assistant-row">
            <div class="assistant-bubble">
                <div class="assistant-label">⚡ Watt</div>
                <div>{_format_answer_html(message["content"])}</div>
                <div class="meta-row">{html.escape(meta_row)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Sources ({len(source_documents)})", expanded=False):
        render_sources(source_documents)

    if settings.get("show_retrieved_context"):
        with st.expander("Retrieved context", expanded=False):
            render_retrieved_context(source_documents)

    if settings.get("show_debug_info"):
        with st.expander("Debug info", expanded=False):
            render_debug_info(message)


def render_message(message, settings):
    if message["role"] == "user":
        render_user_message(message["content"])
    else:
        render_assistant_message(message, settings)


def render_messages(messages, settings):
    for message in messages:
        render_message(message, settings)


def _run_query(query, settings, no_llm):
    start = time.perf_counter()
    strategy_override = get_strategy_override(settings["strategy"])

    result = call_run_agent(
        query,
        no_llm=no_llm,
        top_k=settings["top_k"],
        strategy_override=strategy_override,
    )

    latency = time.perf_counter() - start
    return result, latency


def process_query(query, settings):
    """Add the user message, run the agent, log to MLflow, and store the assistant reply.

    Never crashes the UI: agent failures and MLflow logging failures are both
    caught and surfaced as a message/warning instead of raising.
    """
    st.session_state.messages.append({"role": "user", "content": query})

    # Read every setting fresh, at the moment this specific query is processed
    # (never from a stale snapshot), so toggling "Use LLM" always affects the
    # very next query.
    requested_use_llm = settings["use_llm"]
    llm_status = check_llm_env()
    llm_available = llm_status["available"]
    llm_missing_reason = llm_status["reason"]
    mode, mode_label, mode_reason = compute_llm_mode(requested_use_llm, llm_status)
    effective_use_llm = mode == "llm"
    effective_no_llm = not effective_use_llm

    try:
        with st.spinner("Searching project sources..."):
            result, latency = _run_query(query, settings, effective_no_llm)
    except Exception as exc:
        st.session_state.last_error = str(exc)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Something went wrong while answering this question: {exc}",
            "source_documents": [],
            "debug": {"error": str(exc)},
            "latency_seconds": None,
            "strategy": None,
            "filters": {},
            "grounding_check": None,
        })
        return

    source_documents = extract_source_documents(result)
    raw_answer = result.get("answer")
    visible_answer = clean_assistant_answer(raw_answer, len(source_documents), mode)

    if settings.get("show_debug_info"):
        # Terminal echo of the same fields shown in the in-app debug panel;
        # only printed when debug info is enabled, so it's never noisy by
        # default. Uses errors="replace" because some Windows consoles use a
        # cp1252 encoding that can't render the mode-label arrow character.
        for line in (
            "=== WATT CHAT DEBUG ===",
            f"query: {query}",
            f"requested_use_llm: {requested_use_llm}",
            f"llm_available: {llm_available}",
            f"llm_missing_reason: {llm_missing_reason}",
            f"effective_use_llm: {effective_use_llm}",
            f"no_llm_passed_to_run_agent: {effective_no_llm}",
            f"mode: {mode} ({mode_label})",
            f"strategy: {settings['strategy']}",
            f"strategy_override: {get_strategy_override(settings['strategy'])}",
            f"top_k: {settings['top_k']}",
            f"result keys: {list(result.keys()) if isinstance(result, dict) else []}",
            f"raw answer preview: {(raw_answer or '')[:200]!r}",
            f"visible answer preview: {visible_answer[:200]!r}",
            f"source_document_count: {len(source_documents)}",
            "=======================",
        ):
            print(line.encode("ascii", errors="replace").decode("ascii"))

    strategy_override = get_strategy_override(settings["strategy"])
    mlflow_settings = {
        "top_k": settings["top_k"],
        "use_llm": settings["use_llm"],
        "requested_use_llm": requested_use_llm,
        "llm_available": llm_available,
        "llm_missing_reason": llm_missing_reason,
        "effective_use_llm": effective_use_llm,
        "no_llm": effective_no_llm,
        "mode": mode,
        "mode_label": mode_label,
        "strategy": settings["strategy"],
        "strategy_override": strategy_override,
        "show_retrieved_context": settings["show_retrieved_context"],
        "show_debug_info": settings["show_debug_info"],
    }

    run_id = None
    mlflow_warning = None
    try:
        run_id = call_log_rag_query(
            query=query,
            result=result,
            latency_seconds=latency,
            settings=mlflow_settings,
        )
        st.session_state.last_mlflow_run_id = run_id
    except Exception as exc:
        run_id = None
        mlflow_warning = str(exc)
        st.session_state.last_error = mlflow_warning

    plan = result.get("plan") if isinstance(result.get("plan"), dict) else {}
    safe_result = {
        "query": result.get("query"),
        "plan": plan,
        "strategy": result.get("strategy"),
        "filters": result.get("filters"),
        "prompt": result.get("prompt"),
        "answer": result.get("answer"),
        "grounding_check": result.get("grounding_check"),
        "sources": result.get("sources"),
        "source_documents": source_documents,
    }

    message = {
        "role": "assistant",
        "content": visible_answer,
        "source_documents": source_documents,
        "mode": mode,
        "mode_label": mode_label,
        "debug": {
            "plan": plan,
            "requested_use_llm": requested_use_llm,
            "effective_use_llm": effective_use_llm,
            "no_llm_passed_to_run_agent": effective_no_llm,
            "llm_available": llm_available,
            "llm_missing_reason": llm_missing_reason,
            "mode": mode,
            "mode_label": mode_label,
            "mode_reason": mode_reason,
            "raw_result_answer_preview": (raw_answer or "")[:400],
            "final_visible_answer_preview": visible_answer[:400],
            "mlflow_run_id": run_id,
            "mlflow_warning": mlflow_warning,
            "result_keys": list(result.keys()) if isinstance(result, dict) else [],
            "raw_result_safe": safe_result,
        },
        "latency_seconds": latency,
        "strategy": result.get("strategy"),
        "filters": result.get("filters") if isinstance(result.get("filters"), dict) else {},
        "grounding_check": result.get("grounding_check"),
    }

    st.session_state.messages.append(message)
