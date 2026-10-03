from ledgerlens import agent


def patch_workers(monkeypatch, route):
    calls = []

    def fake_route(question):
        calls.append(("route", question))
        return route

    def fake_retrieve(question):
        calls.append(("retrieve", question))
        return [{"chunk_id": "X-1"}]

    def fake_generate(question, points):
        calls.append(("generate", points))
        return {"answer": "fake answer", "sources": [{"id": 1}]}

    monkeypatch.setattr(agent, "route_question", fake_route)
    monkeypatch.setattr(agent, "retrieve", fake_retrieve)
    monkeypatch.setattr(agent, "generate", fake_generate)
    return calls


def test_lookup_route_runs_retrieve_then_generate(monkeypatch):
    calls = patch_workers(monkeypatch, "lookup")

    result = agent.run("test question")

    assert result["route"] == "lookup"
    assert result["answer"] == "fake answer"
    assert result["sources"] == [{"id": 1}]
    assert calls == [
        ("route", "test question"),
        ("retrieve", "test question"),
        ("generate", [{"chunk_id": "X-1"}]),
    ]


def test_calculate_route_skips_retrieval(monkeypatch):
    calls = patch_workers(monkeypatch, "calculate")

    result = agent.run("how much did sales grow?")

    assert result["route"] == "calculate"
    assert result["answer"] == agent.NOT_SUPPORTED
    assert result["sources"] == []
    assert calls == [("route", "how much did sales grow?")]
