# Watt-the-AI

RAG system over YouTube transcripts/comments, Hacker News discussions, and research sources — with agentic query routing, hybrid retrieval, and optional LLM grounding.

## Quick start

```bash
pip install -r requirements.txt
```

## 1. Generate the databases

The RAG layer reads two SQLite files:

- `src/database/structured_db/structured.db`
- `src/database/vector_db/vector.db`

They are **not** created automatically by the Streamlit app. Build them with the existing pipeline after preprocessing and feature extraction outputs exist.

**Step A — preprocessing** (if not already done):

```bash
python src/preprocessing/preprocessing_run_all.py
```

Outputs land in `data/preprocessing/`.

**Step B — feature extraction** (if not already done):

```bash
python src/feature_extraction/run_all_feature_extraction.py
```

Outputs land in `data/feature_extraction/`.

**Step C — database pipeline**:

```bash
python src/database/execution/run_data_pipeline.py
```

**MLflow-tracked pipeline** (same logic, with metrics and DB artifacts):

```bash
python src/mlflow_tracking/run_tracked_pipeline.py
```

### If databases are missing

The Streamlit app checks for both `.db` files on load. If either is missing, it shows setup instructions and **does not** auto-run the pipeline (Streamlit reruns often; rebuilding DBs would be slow and risky). Use the command above, then refresh the app.

An optional **Admin: build databases** expander in the app can run the same pipeline script manually with a confirmation checkbox.

## 2. Run the Streamlit app

From the project root:

```bash
streamlit run app/streamlit_app.py
```

The sidebar lets you configure:

- **Use LLM** — on/off (retrieval-only shows the assembled prompt/context)
- **Show retrieved context**
- **Top K** (3–10)
- **Retrieval strategy** — `auto` (agent routing) or `hybrid`, `semantic`, `lexical`, `metadata`

Chat history is kept in `st.session_state`. Each query is logged to MLflow when tracking succeeds.

## 3. MLflow UI

Tracking is stored locally in 'mlflow.db' and logged artifacts are stored in 'mlartifacts'. 
To create this file & folder, run:

```bash
python src/mlflow_tracking/run_tracked_pipeline.py
```

To launch the UI, run:

```bash
python src/mlflow_tracking/run_mlflow_ui.py
```

Do **not** use plain `mlflow ui` alone — MLflow 3.x blocks the file store unless `MLFLOW_ALLOW_FILE_STORE=true` is set. The launcher script handles that and points at the correct backend.

Open the URL shown in the terminal (usually http://127.0.0.1:5000).

**Experiments:**

| Experiment | What is logged |
|---|---|
| `watt-the-ai-rag` | Each Streamlit query — params, latency, sources, answer artifacts |
| `watt-the-ai-pipeline` | Database pipeline runs — runtime, DB sizes, optional `.db` artifacts |

If MLflow logging fails, the Streamlit app shows a warning and continues normally.

## 4. CLI agent (existing)

```bash
python src/agentic_orchestration/run_agent.py "your question here"
python src/agentic_orchestration/run_agent.py "your question" --no-llm
```

## 5. Environment variables for LLM usage

| Variable | Purpose |
|---|---|
| `RAG_BIG_LLM_BASE_URL` | Base URL for the main answer LLM (OpenAI-compatible `/v1/chat/completions`) |
| `RAG_BIG_LLM_MODEL` | Model name for the main LLM (default: `local-model`) |
| `RAG_SMALL_LLM_BASE_URL` | Base URL for routing / grounding checks |
| `RAG_SMALL_LLM_MODEL` | Model name for the small LLM (default: `local-small-model`) |

If `RAG_BIG_LLM_BASE_URL` is unset:

- The CLI agent returns a message that the LLM is not configured.
- Streamlit warns you and supports **retrieval-only mode** (disable **Use LLM** in the sidebar).

If `RAG_SMALL_LLM_BASE_URL` is unset, query routing falls back to rule-based planning.

Example (Ollama-style):

```bash
export RAG_BIG_LLM_BASE_URL=http://localhost:11434
export RAG_BIG_LLM_MODEL=llama3
export RAG_SMALL_LLM_BASE_URL=http://localhost:11434
export RAG_SMALL_LLM_MODEL=llama3
```

On Windows PowerShell:

```powershell
$env:RAG_BIG_LLM_BASE_URL = "http://localhost:11434"
$env:RAG_BIG_LLM_MODEL = "llama3"
```

## Project layout (key paths)

```
app/streamlit_app.py              # Streamlit frontend
src/agentic_orchestration/        # Agent graph + LLM client
src/rag/                          # Retrievers, embedder, prompts
src/database/execution/           # Database build pipeline
src/mlflow_tracking/              # MLflow helpers + tracked pipeline wrapper
config/                           # Router / grounding prompts
data/                             # Raw, preprocessed, and feature data
```
