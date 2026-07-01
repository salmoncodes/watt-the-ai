# Watt — Streamlit App Guide

This is the Streamlit frontend for the `watt-the-ai` RAG assistant. It's a
thin UI layer on top of the existing backend (`agentic_orchestration.graph.run_agent`
and `mlflow_tracking.tracking`) — no RAG, retrieval, database, or MLflow logic
lives here.

## Running the app

From the project root:

```bash
streamlit run app/streamlit_app.py
```

The app requires two SQLite databases to already exist:

- `src/database/structured_db/structured.db`
- `src/database/vector_db/vector.db`

If either is missing, the app shows setup instructions instead of the chat
UI (see the top-level `README.md` for how to build them). It never builds
them automatically.

## File structure

```
app/
├── streamlit_app.py     # Entry point / controller — wires everything together
└── ui/
    ├── state.py          # st.session_state helpers (messages, pending query, etc.)
    ├── styles.py         # All injected CSS (dark theme, cards, chat bubbles, input)
    ├── sidebar.py         # Sidebar: brand, New Chat, DB status, settings, MLflow/drift info
    ├── header.py          # Page header (title + subtitle above the chat)
    ├── empty_state.py     # "How can I help you today?" + suggestion cards
    ├── chat.py            # Message rendering + process_query() (calls run_agent + MLflow)
    ├── sources.py         # Source-document extraction and rendering
    ├── debug.py           # "Debug info" expander content
    ├── helpers.py         # Pure helper functions: LLM mode logic, answer cleaning, env checks
    └── services.py        # Thin wrappers around the backend (run_agent, MLflow, drift config)
```

`streamlit_app.py` only orchestrates: it calls into `ui/*` modules and never
implements retrieval, LLM, or MLflow logic directly.

## Navigating the UI

### Sidebar (left)

- **⚡ Watt / + New chat** — clears the conversation, pending query, and last
  MLflow run id.
- **Database status** — pill indicators for `structured.db` / `vector.db`
  (missing / found-but-empty / found-and-populated).
- **Retrieval settings**
  - **Retrieval strategy** — `auto` (agent decides), or force `hybrid`,
    `semantic`, `lexical`, `metadata`.
  - **Top K** — number of retrieved documents (3–10).
- **Generation settings**
  - **Use LLM** — see [LLM modes](#llm-modes-important) below.
  - **Show retrieved context** — adds a plain-text "Retrieved context" expander
    to each answer.
  - **Show debug info** — adds a "Debug info" expander to each answer (see
    [Debug info](#debug-info)).
- **MLflow** — shows the tracking backend (`mlflow.db` + `mlartifacts/`) and
  the command to open the MLflow UI.
- **Drift detection** — shows the `watt-the-ai-drift` experiment name and the
  commands to create a baseline / run a drift check. These are informational
  only — the app never runs drift checks itself.
- **Admin / Database** (expander) — commands to rebuild the databases; not
  run automatically.

### Empty state (center)

Before the first message, you'll see the Watt header and three equal-size
suggestion cards. Clicking **Ask** on a card queues that question exactly
like typing it into the chat box.

### Chat

- Type a question in the message box at the bottom and press Enter.
- Each assistant reply shows a meta row: `Mode · Strategy · Sources · latency`.
- **Sources (N)** expander — every retrieved document, with score, snippet,
  and available metadata (title, URL, published date, etc.).
- **Retrieved context** expander — only shown if "Show retrieved context" is
  enabled; the same documents as plain text.
- **Debug info** expander — only shown if "Show debug info" is enabled.

### LLM modes (important)

The **Use LLM** checkbox and the actual availability of an LLM endpoint
combine into exactly three modes, each with its own distinct message and
`Mode:` label so they can never be confused with each other:

| Mode | When | `Mode:` label | Visible message |
|---|---|---|---|
| Retrieval-only | Use LLM unchecked | `Retrieval-only` | "Retrieval-only mode is active. I found relevant sources below." |
| LLM unavailable | Use LLM checked, but `RAG_BIG_LLM_BASE_URL` isn't set | `LLM unavailable → retrieval-only` | "LLM mode was requested, but the LLM endpoint/config is not available. I used retrieval-only mode and found relevant sources below." |
| LLM | Use LLM checked and the endpoint is configured | `LLM` | The actual generated answer |

If a query has zero retrieved sources, that always takes priority and shows
a "no relevant sources" message instead, regardless of mode.

See [Environment variables for LLM usage](../README.md#5-environment-variables-for-llm-usage)
in the top-level README to configure `RAG_BIG_LLM_BASE_URL` / `RAG_BIG_LLM_MODEL`.

### Debug info

When enabled, each answer's **Debug info** expander shows: strategy,
latency, mode + mode reason, `requested_use_llm` / `llm_available` /
`effective_use_llm` / `no_llm_passed_to_run_agent`, raw vs. final visible
answer previews, filters, plan, grounding check, MLflow run id (or warning),
result keys, and a safe (JSON-serializable) copy of the raw agent result.

## MLflow logging

Every completed query is logged to the `watt-the-ai-rag` experiment
(local SQLite backend: `mlflow.db`, artifacts in `mlartifacts/`) — params,
metrics, and artifacts (answer, prompt, grounding check, sources, plan,
full result, settings). If logging fails, the app shows a warning and keeps
working normally; it never crashes the chat.

```bash
python src/mlflow_tracking/run_mlflow_ui.py
```

## Troubleshooting

- **Stale UI / changes not showing up**: Streamlit can leave old processes
  running on port 8501. Stop the running `streamlit run` process and
  restart it, then hard-refresh the browser tab.
- **"LLM config missing" warning in the sidebar**: `RAG_BIG_LLM_BASE_URL` is
  not set in the environment Streamlit was started from. Set it and restart
  Streamlit (env vars are read at process start).
- **No sources / "No relevant sources were retrieved"**: check the sidebar's
  database status pills — the vector database may be empty or missing.
