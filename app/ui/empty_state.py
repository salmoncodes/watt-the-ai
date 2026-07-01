"""
empty_state.py

The empty conversation state (title + equal-size suggestion cards), plus
the "databases not found" state shown when structured.db/vector.db are
missing.
"""

import html

import streamlit as st

from ui.state import set_pending_query

SUGGESTIONS = [
    "What do people say about data center water use?",
    "Summarize research on AI energy consumption.",
    "What is Hacker News discussing about data centers?",
]


def render_suggestion_cards():
    """Three equal-size suggestion cards; clicking Ask queues the query and reruns."""
    with st.container(key="suggestions"):
        cols = st.columns(3, gap="medium")
        for i, (col, suggestion) in enumerate(zip(cols, SUGGESTIONS)):
            with col:
                st.markdown(
                    f'<div class="suggestion-card">{html.escape(suggestion)}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Ask", key=f"suggestion_{i}", use_container_width=True):
                    set_pending_query(suggestion)
                    st.rerun()


def render_empty_state():
    """Title + suggestion cards shown before the first message."""
    with st.container(key="empty_state_wrapper"):
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-title">How can I help you today?</div>
                <div class="empty-subtitle">
                    Ask about water, energy, data centers, or AI infrastructure.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_suggestion_cards()


def render_missing_db_state(db_status):
    """Shown instead of chat when structured.db/vector.db haven't been generated yet."""
    st.subheader("Databases not found")
    st.caption("To use Watt, generate the database files first.")

    st.markdown("**Run:**")
    st.code("python src/database/execution/run_data_pipeline.py", language="bash")

    st.markdown("**Required outputs:**")
    st.markdown("- `src/database/structured_db/structured.db`")
    st.markdown("- `src/database/vector_db/vector.db`")

    st.caption("If the pipeline fails, make sure data/preprocessing/ and data/feature_extraction/ exist.")

    missing = [name for name, info in (db_status or {}).items() if not info.get("exists")]
    if missing:
        st.error(f"Missing: {', '.join(missing)}")
