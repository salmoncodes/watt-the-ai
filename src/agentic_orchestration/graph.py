from typing import Any, Dict, List, TypedDict
from pathlib import Path

try:
    from langgraph.graph import END, START, StateGraph
except ImportError as exc:
    raise ImportError(
        "Install LangGraph first: pip install langgraph"
    ) from exc

from agentic_orchestration.llm_client import call_llm, call_small_llm
from agentic_orchestration.query_planner import plan_query
from rag.prompting.prompt_builder import build_prompt
from rag.retrieval.registry import get_retriever, list_strategies

ROOT = Path(__file__).resolve().parents[2]
GROUNDING_PROMPT = ROOT / "config" / "rag_grounding_prompt.txt"


class AgentState(TypedDict, total=False):
    query: str
    plan: Dict[str, Any]
    strategy: str
    filters: Dict[str, str]
    docs: List[Any]
    prompt: str
    answer: str
    grounding_check: str
    sources: List[str]
    source_documents: List[Dict[str, Any]]
    no_llm: bool
    top_k: int
    strategy_override: str


def route_query(state: AgentState):
    plan = plan_query(state["query"])

    filters = {}
    if plan.get("source"):
        filters["source"] = plan["source"]
    if plan.get("sentiment"):
        filters["sentiment"] = plan["sentiment"]
    if plan.get("relation_contains"):
        filters["relation_contains"] = plan["relation_contains"]
    if plan.get("keyword"):
        filters["keyword"] = plan["keyword"]

    strategy = "hybrid"
    if filters.get("sentiment") or filters.get("relation_contains"):
        strategy = "metadata"

    strategy_override = state.get("strategy_override")
    if strategy_override:
        if strategy_override not in list_strategies():
            raise ValueError(
                f"Unknown retrieval strategy '{strategy_override}'. "
                f"Available: {', '.join(list_strategies())}"
            )
        strategy = strategy_override

    return {"plan": plan, "filters": filters, "strategy": strategy}


def retrieve_context(state: AgentState):
    query = state["plan"].get("rewritten_query") or state["query"]
    retriever = get_retriever(state["strategy"])
    filters = state.get("filters")
    top_k = state.get("top_k", 6)
    docs = retriever.retrieve(query, top_k=top_k, filters=filters)
    if not docs:
        if filters and filters.get("source"):
            docs = get_retriever("hybrid").retrieve(
                state["query"],
                top_k=top_k,
                filters=filters,
            )
            if docs:
                return {"docs": docs, "strategy": "hybrid"}

        docs = get_retriever("hybrid").retrieve(state["query"], top_k=top_k, filters=None)
        return {"docs": docs, "strategy": "hybrid", "filters": {}}
    return {"docs": docs}


def serialize_doc(doc):
    return {
        "document_id": getattr(doc, "document_id", None),
        "text": getattr(doc, "text", ""),
        "score": getattr(doc, "score", None),
        "source": getattr(doc, "source", None),
        "strategy": getattr(doc, "strategy", None),
        "doc_type": getattr(doc, "doc_type", None),
        "metadata": getattr(doc, "metadata", {}),
    }


def build_grounded_prompt(state: AgentState):
    query = state["plan"].get("rewritten_query") or state["query"]
    task = state["plan"].get("task", "qa")
    docs = state.get("docs", [])
    prompt_data = build_prompt(query, docs, task=task)
    return {
        "prompt": prompt_data["prompt"],
        "sources": prompt_data["sources"],
        "source_documents": [serialize_doc(d) for d in docs],
    }


def generate_answer(state: AgentState):
    if state.get("no_llm"):
        return {
            "answer": (
                "Retrieval-only mode is active, or the LLM did not generate a final "
                "answer. I found relevant sources below."
            )
        }

    answer = call_llm(state["prompt"])
    if not answer:
        answer = "LLM endpoint is not configured. Retrieved prompt is ready."
    return {"answer": answer}


def check_grounding(state: AgentState):
    if state.get("no_llm"):
        return {"grounding_check": "Skipped because no_llm=True"}

    if GROUNDING_PROMPT.exists():
        instructions = GROUNDING_PROMPT.read_text(encoding="utf-8")
    else:
        instructions = "Check if this answer only uses the provided context."

    check_prompt = (
        instructions
        + "\n\n"
        f"Prompt:\n{state['prompt']}\n\nAnswer:\n{state['answer']}"
    )
    check = call_small_llm(check_prompt)
    return {"grounding_check": check or "Grounding check skipped."}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("route_query", route_query)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("build_grounded_prompt", build_grounded_prompt)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("check_grounding", check_grounding)

    builder.add_edge(START, "route_query")
    builder.add_edge("route_query", "retrieve_context")
    builder.add_edge("retrieve_context", "build_grounded_prompt")
    builder.add_edge("build_grounded_prompt", "generate_answer")
    builder.add_edge("generate_answer", "check_grounding")
    builder.add_edge("check_grounding", END)
    return builder.compile()


def run_agent(query, no_llm=False, top_k=6, strategy_override=None):
    graph = build_graph()
    return graph.invoke({
        "query": query,
        "no_llm": no_llm,
        "top_k": top_k,
        "strategy_override": strategy_override,
    })
