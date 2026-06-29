# RAG Layer

A toolbox for retrieval and structured prompting. It exposes capabilities; it
does NOT make decisions. Specifically, this layer does **not** select a
retrieval strategy, call an LLM, or route queries -- those belong to the agent
layer next door.

## What it exposes

- `representation/embedder.py` -- embed a query into the ingestion vector space.
- `retrieval/` -- four interchangeable strategies behind one interface:
  - `semantic` -- embedding similarity (meaning).
  - `lexical` -- FTS5 / BM25 (exact terms, names, numbers).
  - `metadata` -- structured-field lookup over structured.db (source, sentiment, keyword).
  - `hybrid` -- reciprocal-rank fusion of semantic + lexical.
  - selected by name via `retrieval/registry.py`: `get_retriever("semantic")`.
- `prompting/prompt_builder.py` -- assemble a grounded prompt for a task
  (`qa`, `summarize`, `sentiment_insight`); returns the prompt + source ids and stops.

## Contract for the agent layer

```
docs   = get_retriever(strategy).retrieve(query, top_k=k, filters={...})
prompt = build_prompt(query, docs, task=task)["prompt"]
# the agent chose `strategy` and `task`, and the agent calls the LLM with `prompt`.
```

## Prerequisites

- The database layer must have been run (structured.db and vector.db exist).
- `rag_config.EMBEDDING_MODEL` must match the model used in transfer_to_vector.py.
