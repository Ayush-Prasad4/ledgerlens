import sys
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ledgerlens.ask import generate, retrieve


class AgentState(TypedDict, total=False):
    question: str
    points: list
    answer: str
    sources: list


def retrieve_node(state: AgentState) -> dict:
    return {"points": retrieve(state["question"])}


def generate_node(state: AgentState) -> dict:
    result = generate(state["question"], state["points"])
    return {"answer": result["answer"], "sources": result["sources"]}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)
    return builder.compile()


def run(question: str) -> dict:
    final = build_graph().invoke({"question": question})
    return {
        "question": question,
        "answer": final["answer"],
        "sources": final["sources"],
    }


def main():
    result = run(sys.argv[1])
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"[{s['id']}] {s['ticker']} FY{s['fiscal_year']} | {s['section']}")


if __name__ == "__main__":
    main()
