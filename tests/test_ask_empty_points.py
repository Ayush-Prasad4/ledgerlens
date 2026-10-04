from ledgerlens import ask


def test_empty_points_do_not_call_llm(monkeypatch):
    def boom():
        raise AssertionError("LLM must not be called when there are no points")

    monkeypatch.setattr(ask, "get_llm", boom)
    out = ask.generate("What was Meta's total revenue in 2023?", [])
    assert out["answer"] == ask.NOT_FOUND
    assert out["sources"] == []
