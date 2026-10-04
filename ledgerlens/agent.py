import sys
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ledgerlens.ask import generate
from ledgerlens.calculate import FAILURE_PREFIX, calculate_answer
from ledgerlens.lookup_retrieval import retrieve_lookup as retrieve
from ledgerlens.router import route_question
from ledgerlens.sanity import sanity_check


class AgentState(TypedDict, total=False):
    question: str
    route: str
    points: list
    answer: str
    sources: list
    calculation: dict


def route_node(state: AgentState) -> dict:
    return {"route": route_question(state["question"])}


def pick_path(state: AgentState) -> str:
    return state["route"]


def retrieve_node(state: AgentState) -> dict:
    return {"points": retrieve(state["question"])}


def generate_node(state: AgentState) -> dict:
    result = generate(state["question"], state["points"])
    return {"answer": result["answer"], "sources": result["sources"]}


def calculate_node(state: AgentState) -> dict:
    result = calculate_answer(state["question"])
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "calculation": result["calculation"],
    }


def check_node(state: AgentState) -> dict:
    """Sanity gate after the calculation: replace the answer with a refusal if it fails."""
    calc = state.get("calculation") or {}
    if not calc.get("ok"):
        return {"answer": state["answer"]}  # already a refusal, nothing to check
    ok, reason = sanity_check(state["question"], calc)
    if ok:
        return {"answer": state["answer"]}  # unchanged
    return {
        "answer": FAILURE_PREFIX + reason,
        "sources": [],
        "calculation": {"ok": False, "error": reason},
    }


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("route", route_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_node("calculate", calculate_node)
    builder.add_node("check", check_node)
    builder.add_edge(START, "route")
    builder.add_conditional_edges(
        "route", pick_path, {"lookup": "retrieve", "calculate": "calculate"}
    )
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)
    builder.add_edge("calculate", "check")
    builder.add_edge("check", END)
    return builder.compile()


def run(question: str) -> dict:
    final = build_graph().invoke({"question": question})
    return {
        "question": question,
        "route": final["route"],
        "answer": final["answer"],
        "sources": final["sources"],
        "calculation": final.get("calculation"),
    }


def main():
    result = run(sys.argv[1])
    print(f"Route: {result['route']}\n")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"[{s['id']}] {s['ticker']} FY{s['fiscal_year']} | {s['section']}")


if __name__ == "__main__":
    main()
