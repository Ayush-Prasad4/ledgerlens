import pytest
from openai import OpenAIError

from ledgerlens import lookup_retrieval as lr


def chunk(cid):
    return {"chunk_id": cid}


def ids(points):
    return [p["chunk_id"] for p in points]


def test_merge_keeps_base_order_and_adds_new_chunks():
    out = lr.merge_extras([chunk("A"), chunk("B")], [chunk("C"), chunk("D")])
    assert ids(out) == ["A", "B", "C", "D"]


def test_merge_skips_duplicates_and_respects_limit():
    extra = [chunk("B"), chunk("C"), chunk("D"), chunk("E"), chunk("F")]
    out = lr.merge_extras([chunk("A"), chunk("B")], extra)
    assert ids(out) == ["A", "B", "C", "D", "E"]


def test_retrieve_lookup_appends_planner_chunks(monkeypatch):
    monkeypatch.setattr(lr, "base_retrieve", lambda q: [chunk("A"), chunk("B")])
    monkeypatch.setattr(lr, "plan_metrics", lambda q: ["Net sales"])
    monkeypatch.setattr(lr, "retrieve_for_metrics", lambda m, t, y: [chunk("B"), chunk("C"), chunk("D")])
    out = lr.retrieve_lookup("What were Apple's net sales in fiscal 2024?")
    assert ids(out) == ["A", "B", "C", "D"]


def test_no_ticker_means_planner_is_not_called(monkeypatch):
    def boom(q):
        raise AssertionError("planner must not be called")

    monkeypatch.setattr(lr, "base_retrieve", lambda q: [chunk("A")])
    monkeypatch.setattr(lr, "plan_metrics", boom)
    assert ids(lr.retrieve_lookup("Tell me about supply chain risks")) == ["A"]


@pytest.mark.parametrize("error", [ValueError("bad plan"), OpenAIError("down")])
def test_planner_failure_falls_back_to_base(monkeypatch, error):
    def fail(q):
        raise error

    monkeypatch.setattr(lr, "base_retrieve", lambda q: [chunk("A")])
    monkeypatch.setattr(lr, "plan_metrics", fail)
    out = lr.retrieve_lookup("What were Apple's net sales in fiscal 2024?")
    assert ids(out) == ["A"]
