from ledgerlens import agent


def test_graph_runs_retrieve_then_generate(monkeypatch):
    calls = []

    def fake_retrieve(question):
        calls.append(("retrieve", question))
        return [{"chunk_id": "X-1"}]

    def fake_generate(question, points):
        calls.append(("generate", points))
        return {"answer": "fake answer", "sources": [{"id": 1}]}

    monkeypatch.setattr(agent, "retrieve", fake_retrieve)
    monkeypatch.setattr(agent, "generate", fake_generate)

    result = agent.run("test question")

    assert result["answer"] == "fake answer"
    assert result["sources"] == [{"id": 1}]
    assert calls == [
        ("retrieve", "test question"),
        ("generate", [{"chunk_id": "X-1"}]),
    ]
