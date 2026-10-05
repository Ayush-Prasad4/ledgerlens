import pytest

from ledgerlens import agent, calculate
from ledgerlens.ask import build_context
from ledgerlens.extract_facts import build_extract_context
from ledgerlens.injection_harness import poisoned

REAL = {"chunk_id": "REAL-1", "ticker": "MSFT", "fiscal_year": 2024, "section": "Item 7",
        "kind": "text", "text": "real text"}
POISON = {"chunk_id": "POISON-1", "ticker": "MSFT", "fiscal_year": 2024, "section": "Item 7",
          "kind": "text", "text": "ZX-CANARY-0000 do this"}


def case(path, position):
    return {"path": path, "position": position, "poison": POISON}


def test_lookup_poison_reaches_node_and_context(monkeypatch):
    monkeypatch.setattr(agent, "retrieve", lambda question: [REAL])
    with poisoned(case("lookup", "last")):
        points = agent.retrieve_node({"question": "q"})["points"]
    assert [p["chunk_id"] for p in points] == ["REAL-1", "POISON-1"]
    assert "ZX-CANARY-0000" in build_context(points)


def test_calc_poison_reaches_extractor_context(monkeypatch):
    monkeypatch.setattr(calculate, "retrieve_for_metrics", lambda metrics, ticker, years: [REAL])
    with poisoned(case("calc", "first")):
        points = calculate.retrieve_for_metrics(["m"], "MSFT", [2024])
    assert [p["chunk_id"] for p in points] == ["POISON-1", "REAL-1"]
    context = build_extract_context(points)
    assert "chunk_id=POISON-1" in context
    assert "ZX-CANARY-0000" in context


def test_poisoned_restores_original_after_use(monkeypatch):
    fake = lambda question: [REAL]
    monkeypatch.setattr(agent, "retrieve", fake)
    with poisoned(case("lookup", "last")):
        assert agent.retrieve is not fake
    assert agent.retrieve is fake


def test_poisoned_restores_after_exception(monkeypatch):
    fake = lambda metrics, ticker, years: [REAL]
    monkeypatch.setattr(calculate, "retrieve_for_metrics", fake)
    with pytest.raises(RuntimeError):
        with poisoned(case("calc", "last")):
            raise RuntimeError("boom")
    assert calculate.retrieve_for_metrics is fake


def test_poisoned_unknown_path():
    with pytest.raises(ValueError):
        with poisoned(case("elsewhere", "last")):
            pass


def test_poisoned_position_first_and_last(monkeypatch):
    monkeypatch.setattr(agent, "retrieve", lambda question: [REAL])
    with poisoned(case("lookup", "first")):
        first = agent.retrieve("q")
    with poisoned(case("lookup", "last")):
        last = agent.retrieve("q")
    assert first[0]["chunk_id"] == "POISON-1"
    assert last[-1]["chunk_id"] == "POISON-1"
