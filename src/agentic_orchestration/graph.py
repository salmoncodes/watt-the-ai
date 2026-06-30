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
from rag.retrieval.registry import get_retriever

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
    no_llm: bool


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

    return {"plan": plan, "filters": filters, "strategy": strategy}


def retrieve_context(state: AgentState):
    query = state["plan"].get("rewritten_query") or state["query"]
    retriever = get_retriever(state["strategy"])
    filters = state.get("filters")
    docs = retriever.retrieve(query, top_k=6, filters=filters)
    if not docs:
        if filters and filters.get("source"):
            docs = get_retriever("hybrid").retrieve(
                state["query"],
                top_k=6,
                filters=filters,
            )
            if docs:
                return {"docs": docs, "strategy": "hybrid"}

        docs = get_retriever("hybrid").retrieve(state["query"], top_k=6, filters=None)
        return {"docs": docs, "strategy": "hybrid", "filters": {}}
    return {"docs": docs}


def build_grounded_prompt(state: AgentState):
    query = state["plan"].get("rewritten_query") or state["query"]
    task = state["plan"].get("task", "qa")
    prompt_data = build_prompt(query, state.get("docs", []), task=task)
    return {"prompt": prompt_data["prompt"], "sources": prompt_data["sources"]}


def generate_answer(state: AgentState):
    if state.get("no_llm"):
        return {"answer": state["prompt"]}

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


def run_agent(query, no_llm=False):
    graph = build_graph()
    return graph.invoke({"query": query, "no_llm": no_llm})
