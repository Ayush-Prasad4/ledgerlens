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

    def fake_calculate(question):
        calls.append(("calculate", question))
        return {
            "answer": "calc answer",
            "sources": [{"id": 1}],
            "calculation": {"ok": True},
        }

    monkeypatch.setattr(agent, "route_question", fake_route)
    monkeypatch.setattr(agent, "retrieve", fake_retrieve)
    monkeypatch.setattr(agent, "generate", fake_generate)
    monkeypatch.setattr(agent, "calculate_answer", fake_calculate)
    return calls


def test_lookup_route_runs_retrieve_then_generate(monkeypatch):
    calls = patch_workers(monkeypatch, "lookup")

    result = agent.run("test question")

    assert result["route"] == "lookup"
    assert result["answer"] == "fake answer"
    assert result["sources"] == [{"id": 1}]
    assert result["calculation"] is None
    assert calls == [
        ("route", "test question"),
        ("retrieve", "test question"),
        ("generate", [{"chunk_id": "X-1"}]),
    ]


def test_calculate_route_uses_calculate_answer(monkeypatch):
    calls = patch_workers(monkeypatch, "calculate")

    result = agent.run("how much did sales grow?")

    assert result["route"] == "calculate"
    assert result["answer"] == "calc answer"
    assert result["sources"] == [{"id": 1}]
    assert result["calculation"] == {"ok": True}
    assert calls == [
        ("route", "how much did sales grow?"),
        ("calculate", "how much did sales grow?"),
    ]
