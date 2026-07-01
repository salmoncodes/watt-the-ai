import argparse
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_orchestration.graph import run_agent


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--strategy", choices=["hybrid", "semantic", "lexical", "metadata"])
    args = parser.parse_args()

    result = run_agent(
        args.query,
        no_llm=args.no_llm,
        top_k=args.top_k,
        strategy_override=args.strategy,
    )
    output = {
        "query": result["query"],
        "plan": result["plan"],
        "strategy": result["strategy"],
        "filters": result["filters"],
        "sources": result.get("sources", []),
        "docs": result.get("source_documents", []),
        "answer": result["answer"],
        "grounding_check": result["grounding_check"],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
