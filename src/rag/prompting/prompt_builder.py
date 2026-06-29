"""
prompt_builder.py
Turns a query + retrieved documents into a grounded, structured prompt. This is
the last thing the RAG layer does: it returns the assembled prompt and the list
of source ids, and stops. It never calls an LLM and never decides which task to
run -- the agent layer chooses the task and makes the call.
"""

from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"
TASK_TEMPLATES = {
    "qa": "qa.txt",
    "summarize": "summarize.txt",
    "sentiment_insight": "sentiment_insight.txt",
}


def _load_template(task):
    if task not in TASK_TEMPLATES:
        raise ValueError(f"Unknown task '{task}'. Available: {', '.join(TASK_TEMPLATES)}")
    return (TEMPLATE_DIR / TASK_TEMPLATES[task]).read_text(encoding="utf-8")


def format_context(retrieved_docs):
    """Render retrieved documents into numbered, citable context blocks."""
    blocks = []
    for i, d in enumerate(retrieved_docs, 1):
        header = f"[{i}] source={d.source} type={d.doc_type} id={d.document_id}"
        blocks.append(f"{header}\n{d.text}")
    return "\n\n".join(blocks)


def build_prompt(query, retrieved_docs, task="qa"):
    """Return a structured prompt object: the prompt text, the task, and the
    ordered source ids (so the agent can map citations back to documents)."""
    template = _load_template(task)
    context = format_context(retrieved_docs)
    prompt = template.format(query=query, context=context)
    return {
        "task": task,
        "prompt": prompt,
        "sources": [d.document_id for d in retrieved_docs],
    }
