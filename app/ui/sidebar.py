"""
sidebar.py

Sidebar rendering: brand, New Chat button, database status, retrieval /
generation settings, MLflow info, drift-detection commands, and the
admin/database expander.

Only displays drift-detection commands -- never runs them from Streamlit.
"""

import html
from pathlib import Path

import streamlit as st

from ui.state import clear_chat
from ui.helpers import count_vector_documents, check_llm_env
from ui.services import (
    check_database_status,
    get_mlflow_tracking_paths,
    DRIFT_EXPERIMENT_NAME,
)

STRATEGY_OPTIONS = ["auto", "hybrid", "semantic", "lexical", "metadata"]


def _status_pill_html(label, level):
    return f'<span class="status-pill status-{level}">{html.escape(label)}</span>'


def _describe_db_state(info):
    if not info.get("exists"):
        return "Missing", "danger"
    tables = info.get("tables") or {}
    counted = [v for v in tables.values() if isinstance(v, int)]
    if counted and sum(counted) == 0:
        return "Found but empty", "warn"
    return "Found and populated", "ok"


def _render_brand():
    st.markdown("### ⚡ Watt")
    st.caption("RAG assistant for water, energy & data centers")


def _render_new_chat_button():
    if st.button("+ New chat", use_container_width=True, key="sidebar_new_chat"):
        clear_chat()
        st.rerun()


def _render_database_status(db_status, vector_counts):
    structured = db_status.get("structured_db") or {}
    vector = db_status.get("vector_db") or {}

    structured_label, structured_level = _describe_db_state(structured)
    st.markdown(
        f"structured.db&nbsp;&nbsp;{_status_pill_html(structured_label, structured_level)}",
        unsafe_allow_html=True,
    )

    vector_label, vector_level = _describe_db_state(vector)
    if vector.get("exists") and vector_counts["total"] == 0:
        vector_label, vector_level = "Found but empty", "warn"
    st.markdown(
        f"vector.db&nbsp;&nbsp;{_status_pill_html(vector_label, vector_level)}",
        unsafe_allow_html=True,
    )

    if vector.get("exists") and vector_counts["total"] == 0:
        st.warning("Vector DB exists but contains 0 documents. Retrieval may return no sources.")


def _render_retrieval_settings():
    strategy = st.selectbox("Retrieval strategy", options=STRATEGY_OPTIONS, index=0)
    top_k = st.slider("Top K", min_value=3, max_value=10, value=5)
    return strategy, top_k


def _render_generation_settings():
    llm_status = check_llm_env()
    llm_available = llm_status["available"]
    # Checkbox stays enabled even when config is missing: the checked state is
    # still recorded as requested_use_llm=True, the app just falls back to
    # retrieval-only and says so explicitly (see mode_label in chat responses).
    use_llm = st.checkbox("Use LLM", value=llm_available)
    show_retrieved_context = st.checkbox("Show retrieved context", value=False)
    show_debug_info = st.checkbox("Show debug info", value=False)
    if not llm_available:
        st.warning(
            "LLM config missing. If you check Use LLM, the app will fall back "
            "to retrieval-only mode."
        )
    return use_llm, show_retrieved_context, show_debug_info


def _render_mlflow_section():
    st.caption("MLflow tracking: enabled")
    tracking_paths = get_mlflow_tracking_paths()
    if tracking_paths:
        st.caption(f"Backend: {Path(tracking_paths['tracking_db']).name}")
        st.caption(f"Artifacts: {Path(tracking_paths['artifact_root']).name}/")
    else:
        st.caption("Backend: mlflow.db")
        st.caption("Artifacts: mlartifacts/")
    st.caption("Open the MLflow UI:")
    st.code("python src/mlflow_tracking/run_mlflow_ui.py", language="bash")


def _render_drift_section():
    st.caption(
        "Lightweight drift monitoring compares current data/retrieval "
        "behavior against a saved baseline."
    )
    st.caption(f"Experiment: {DRIFT_EXPERIMENT_NAME}")
    st.caption("Create a baseline (once):")
    st.code("python src/mlflow_tracking/run_drift_check.py --create-baseline", language="bash")
    st.caption("Run a drift check:")
    st.code("python src/mlflow_tracking/run_drift_check.py", language="bash")
    st.caption("Drift checks are run manually from a terminal, not from this app.")


def _render_admin_section():
    with st.expander("Admin / Database", expanded=False):
        st.caption("Build database pipeline:")
        st.code("python src/database/execution/run_data_pipeline.py", language="bash")
        st.caption("Vector-only rebuild:")
        st.code("python src/database/vector_db/transfer_to_vector.py", language="bash")
        st.caption("Requires data/preprocessing/ and data/feature_extraction/ outputs.")


def render_sidebar():
    """Render the full sidebar and return the current settings dict."""
    _render_brand()
    _render_new_chat_button()

    db_status = check_database_status()
    vector_counts = count_vector_documents(db_status)

    st.markdown("---")
    st.markdown("**Database status**")
    _render_database_status(db_status, vector_counts)

    st.markdown("---")
    st.markdown("**Retrieval settings**")
    strategy, top_k = _render_retrieval_settings()

    st.markdown("---")
    st.markdown("**Generation settings**")
    use_llm, show_retrieved_context, show_debug_info = _render_generation_settings()

    st.markdown("---")
    st.markdown("**MLflow**")
    _render_mlflow_section()

    st.markdown("---")
    st.markdown("**Drift detection**")
    _render_drift_section()

    st.markdown("---")
    _render_admin_section()

    return {
        "strategy": strategy,
        "top_k": top_k,
        "use_llm": use_llm,
        "show_retrieved_context": show_retrieved_context,
        "show_debug_info": show_debug_info,
    }
