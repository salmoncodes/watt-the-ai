"""
header.py

Top page header: a plain, unboxed title + subtitle. No card, no border,
no background, and no New Chat button (that lives in the sidebar now --
see sidebar.py).
"""

import streamlit as st


def render_header():
    """Render the centered ⚡ Watt title and subtitle above the chat area."""
    st.markdown(
        """
        <div class="watt-header">
            <div class="watt-header-title">⚡ Watt</div>
            <div class="watt-header-subtitle">Water, energy &amp; data centers</div>
            <div class="watt-header-subtitle">
                Ask questions grounded in YouTube, Hacker News, and research sources.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
