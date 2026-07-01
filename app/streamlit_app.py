"""
streamlit_app.py

Minimal, dark, ChatGPT/Claude-style frontend for the watt-the-ai RAG agent.

This file is the main controller only: it wires together the app/ui/
modules on top of the existing, unmodified backend
(agentic_orchestration.graph.run_agent + mlflow_tracking.tracking). See
app/ui/ for styling, state, sidebar, header, empty state, chat, sources,
and debug rendering.

No RAG/retrieval/database/MLflow logic is implemented or duplicated here.
"""

import sys
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Watt",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
APP_DIR = Path(__file__).resolve().parent

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from ui.styles import inject_css
from ui.state import init_session_state, set_pending_query, consume_pending_query
from ui.sidebar import render_sidebar
from ui.header import render_header
from ui.empty_state import render_empty_state, render_missing_db_state
from ui.chat import render_messages, process_query
from ui.services import check_database_status
from ui.helpers import count_vector_documents


def main():
    inject_css()
    init_session_state()

    with st.sidebar:
        settings = render_sidebar()

    db_status = check_database_status()
    vector_counts = count_vector_documents(db_status)
    db_ready = bool(db_status["structured_db"].get("exists")) and bool(db_status["vector_db"].get("exists"))

    left, center, right = st.columns([1.25, 2.6, 1.25])
    with center:
        render_header()

        if not db_ready:
            render_missing_db_state(db_status)
        else:
            if vector_counts["total"] == 0:
                st.warning(
                    "The vector database exists but contains 0 documents. "
                    "Retrieval may return no sources. "
                    "Run: `python src/database/vector_db/transfer_to_vector.py`"
                )

            if not st.session_state.messages:
                render_empty_state()
            else:
                render_messages(st.session_state.messages, settings)

    if db_ready:
        prompt = st.chat_input("Message Watt...")
        if prompt:
            set_pending_query(prompt)
            st.rerun()

        pending_query = consume_pending_query()
        if pending_query:
            process_query(pending_query, settings)
            st.rerun()


if __name__ == "__main__":
    main()
