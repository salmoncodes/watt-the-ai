"""
styles.py

All CSS for the Watt frontend, injected once via inject_css(). Keeping
every style rule in one place means the rest of app/ui/ only ever emits
plain HTML with class names -- no inline style blocks scattered around.
"""

import streamlit as st

_CSS = """
<style>
/* ------------------------------------------------------------------ */
/* Page background                                                     */
/* ------------------------------------------------------------------ */
.stApp {
    background: #1F2933;
    color: #F9FAFB;
}

.block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 1180px;
    padding-top: 4.5rem;
    padding-bottom: 8rem;
}

/* ------------------------------------------------------------------ */
/* Sidebar                                                              */
/* ------------------------------------------------------------------ */
section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #374151;
}

section[data-testid="stSidebar"] * {
    color: #F9FAFB;
}

section[data-testid="stSidebar"] .stMarkdown p {
    color: #CBD5E1;
}

/* Sidebar "New chat" button: near-full width, dark, subtle border,
   accent on hover (shares .stButton styling below, near-full width via
   use_container_width=True in sidebar.py). */
section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    font-weight: 600;
}

/* ------------------------------------------------------------------ */
/* Top header (plain text, no card/box)                                */
/* ------------------------------------------------------------------ */
.watt-header {
    text-align: center;
    margin: 6px 0 30px 0;
}

.watt-header-title {
    color: #F9FAFB;
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}

.watt-header-subtitle {
    color: #94A3B8;
    font-size: 0.95rem;
    margin-top: 6px;
}

/* ------------------------------------------------------------------ */
/* Empty state                                                         */
/* ------------------------------------------------------------------ */
.st-key-empty_state_wrapper {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 40vh;
    padding: 12px 0 4px 0;
}

.empty-state {
    text-align: center;
    margin: 0 auto 32px auto;
}

.empty-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #F9FAFB;
}

.empty-subtitle {
    color: #CBD5E1;
    margin-top: 6px;
}

/* ------------------------------------------------------------------ */
/* Suggestion cards (equal width/height, text does not change size)    */
/* ------------------------------------------------------------------ */
.st-key-suggestions [data-testid="stVerticalBlock"] {
    gap: 0rem !important;
}

.suggestion-card {
    background: #2F3A46;
    border: 1px solid #4B5563;
    border-bottom: none;
    border-radius: 18px 18px 0 0;
    padding: 20px 18px;
    height: 150px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
    color: #F9FAFB;
    font-size: 0.95rem;
    line-height: 1.5;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    overflow: hidden;
}

.st-key-suggestions .stButton > button {
    width: 100%;
    margin-top: 0 !important;
    border: 1px solid #4B5563 !important;
    border-top: none !important;
    border-radius: 0 0 18px 18px !important;
    background: #27323F !important;
    color: #A5B4FC !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}

.st-key-suggestions .stButton > button:hover {
    background: #3730A3 !important;
    color: #F9FAFB !important;
    border-color: #4B5563 !important;
}

/* ------------------------------------------------------------------ */
/* Message bubbles                                                     */
/* ------------------------------------------------------------------ */
.message-row {
    display: flex;
    width: 100%;
    margin: 14px 0;
}

.user-row {
    justify-content: flex-end;
}

.assistant-row {
    justify-content: flex-start;
}

.user-bubble {
    background: #3B4856;
    color: #F9FAFB;
    padding: 13px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 72%;
    line-height: 1.55;
}

.assistant-bubble {
    background: #2F3A46;
    color: #F9FAFB;
    border: 1px solid #4B5563;
    padding: 15px 17px;
    border-radius: 18px 18px 18px 4px;
    max-width: 82%;
    line-height: 1.6;
    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
}

.assistant-label {
    color: #A5B4FC;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 6px;
}

.meta-row {
    color: #94A3B8;
    font-size: 0.78rem;
    margin-top: 8px;
}

/* ------------------------------------------------------------------ */
/* Source cards                                                        */
/* ------------------------------------------------------------------ */
.source-card {
    background: #2F3A46;
    border: 1px solid #4B5563;
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
    color: #F9FAFB;
}

.muted-label {
    color: #94A3B8;
}

.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
}

.status-ok {
    background: rgba(52, 211, 153, 0.16);
    color: #34D399;
}

.status-warn {
    background: rgba(251, 191, 36, 0.16);
    color: #FBBF24;
}

.status-danger {
    background: rgba(248, 113, 113, 0.16);
    color: #F87171;
}

/* ------------------------------------------------------------------ */
/* Debug / retrieved-context expanders                                 */
/* ------------------------------------------------------------------ */
[data-testid="stExpander"] {
    background: #27323F;
    border: 1px solid #4B5563;
    border-radius: 14px;
}

/* ------------------------------------------------------------------ */
/* Generic buttons                                                     */
/* ------------------------------------------------------------------ */
.stButton > button {
    border-radius: 14px !important;
    border: 1px solid #4B5563 !important;
    background: #2F3A46 !important;
    color: #F9FAFB !important;
    padding: 0.6rem 0.9rem !important;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    border-color: #818CF8 !important;
    color: #F9FAFB !important;
    background: #3730A3 !important;
}

/* ------------------------------------------------------------------ */
/* Chat input                                                           */
/* ------------------------------------------------------------------ */
/* Streamlit wraps the chat input in several nested containers (stBottom,
   stBottomBlockContainer, and internal divs/section/form around the
   textarea itself), each of which can carry the theme's default panel
   background/border/shadow. All of them are neutralized here; the only
   visible shape should be the textarea styled further down. The
   "FINAL CHAT INPUT OVERRIDES" block at the end of this stylesheet is the
   single source of truth for sizing/scrollbar and wins any specificity
   ties with these resets. */
[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
    border-top: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
}

[data-testid="stBottomBlockContainer"] > div,
[data-testid="stBottomBlockContainer"] > div > div,
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div,
[data-testid="stChatInput"] form,
[data-testid="stChatInput"] section,
[data-testid="stChatInput"] div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

/* ------------------------------------------------------------------ */
/* Sidebar open/collapse button (lighter, visible on dark background)  */
/* ------------------------------------------------------------------ */
button[kind="header"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    color: #CBD5E1 !important;
}

[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {
    color: #CBD5E1 !important;
    fill: #CBD5E1 !important;
}

button[kind="header"]:hover,
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapseButton"]:hover {
    color: #F9FAFB !important;
}

button[kind="header"]:hover svg,
[data-testid="collapsedControl"]:hover svg,
[data-testid="stSidebarCollapseButton"]:hover svg {
    color: #F9FAFB !important;
    fill: #F9FAFB !important;
}

/* ------------------------------------------------------------------ */
/* FINAL CHAT INPUT OVERRIDES                                          */
/* ------------------------------------------------------------------ */
/* Remove the bottom wrapper/card behind the input */
[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
    border-top: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
}

/* Remove nested background boxes around chat input */
[data-testid="stBottomBlockContainer"] > div,
[data-testid="stBottomBlockContainer"] > div > div,
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div,
[data-testid="stChatInput"] form,
[data-testid="stChatInput"] section {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Keep only the actual textarea styled */
[data-testid="stChatInput"] {
    max-width: 920px !important;
    margin: 0 auto 22px auto !important;
    padding: 0 18px !important;
}

/* Main textbox */
[data-testid="stChatInput"] textarea {
    background: #2F3A46 !important;
    color: #F9FAFB !important;
    border: 1px solid #4B5563 !important;
    border-radius: 24px !important;

    min-height: 64px !important;
    max-height: 64px !important;

    font-size: 16px !important;
    line-height: 1.55 !important;

    padding: 18px 62px 18px 24px !important;

    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.28) !important;

    overflow-y: hidden !important;
    resize: none !important;
    scrollbar-width: none !important;
}

/* Hide scrollbar on Chromium browsers */
[data-testid="stChatInput"] textarea::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}

/* Placeholder */
[data-testid="stChatInput"] textarea::placeholder {
    color: #94A3B8 !important;
    font-size: 16px !important;
}

/* Send button */
[data-testid="stChatInput"] button {
    background: #818CF8 !important;
    color: #111827 !important;
    border-radius: 16px !important;
    box-shadow: none !important;
}

/* Remove focus weirdness */
[data-testid="stChatInput"] textarea:focus {
    border-color: #818CF8 !important;
    box-shadow: 0 0 0 1px rgba(129, 140, 248, 0.45),
                0 12px 28px rgba(0, 0, 0, 0.28) !important;
    outline: none !important;
}
</style>
"""


def inject_css():
    """Inject the full Watt stylesheet. Call once, near the top of the app."""
    st.markdown(_CSS, unsafe_allow_html=True)
