"""
debug.py

Debug panel for a single assistant message. Only rendered when the
sidebar's "Show debug info" setting is enabled -- never shown by default.
"""

import streamlit as st


def render_debug_info(message):
    """Strategy, filters, plan, latency, grounding check, MLflow run id, raw result."""
    debug = message.get("debug") or {}

    st.markdown(f"**Strategy:** {message.get('strategy')}")
    st.markdown(f"**Latency (s):** {message.get('latency_seconds')}")

    st.markdown(f"**Mode:** {debug.get('mode')} ({debug.get('mode_label')})")
    st.markdown(f"**Mode reason:** {debug.get('mode_reason')}")
    st.markdown(f"**Requested Use LLM:** {debug.get('requested_use_llm')}")
    st.markdown(f"**LLM available (env configured):** {debug.get('llm_available')}")
    if not debug.get("llm_available"):
        st.markdown(f"**LLM missing reason:** {debug.get('llm_missing_reason')}")
    st.markdown(f"**Effective Use LLM:** {debug.get('effective_use_llm')}")
    st.markdown(f"**no_llm passed to run_agent:** {debug.get('no_llm_passed_to_run_agent')}")

    st.markdown("**Raw result answer (preview):**")
    st.code(debug.get("raw_result_answer_preview") or "", language=None)
    st.markdown("**Final visible answer (preview):**")
    st.code(debug.get("final_visible_answer_preview") or "", language=None)

    st.markdown("**Filters:**")
    st.json(message.get("filters") or {})

    st.markdown("**Plan:**")
    st.json(debug.get("plan") or {})

    st.markdown("**Grounding check:**")
    st.code(message.get("grounding_check") or "", language=None)

    st.markdown(f"**MLflow run id:** {debug.get('mlflow_run_id')}")
    if debug.get("mlflow_warning"):
        st.markdown(f"**MLflow warning:** {debug.get('mlflow_warning')}")

    st.markdown("**Result keys:**")
    st.json(debug.get("result_keys") or [])

    if debug.get("raw_result_safe") is not None:
        st.markdown("**Raw result (safe):**")
        st.json(debug.get("raw_result_safe"))
