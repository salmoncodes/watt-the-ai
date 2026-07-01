"""
state.py

Session state helpers for the Watt chat UI. Keeps all direct
st.session_state access in one place.
"""

import streamlit as st


def init_session_state():
    """Create every session-state key used by the app, if missing."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None
    if "last_mlflow_run_id" not in st.session_state:
        st.session_state.last_mlflow_run_id = None
    if "last_error" not in st.session_state:
        st.session_state.last_error = None


def clear_chat():
    """Reset the conversation (used by the sidebar New Chat button)."""
    st.session_state.messages = []
    st.session_state.pending_query = None
    st.session_state.last_mlflow_run_id = None
    st.session_state.last_error = None


def set_pending_query(query):
    """Queue a query (from chat input or a suggestion card) to be processed on rerun."""
    st.session_state.pending_query = query


def consume_pending_query():
    """Pop and return the pending query, if any, clearing it so it only runs once."""
    query = st.session_state.get("pending_query")
    st.session_state.pending_query = None
    return query
