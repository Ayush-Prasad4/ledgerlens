import pytest

from ledgerlens import calculate
from ledgerlens.injection_harness import poisoned

POISON = {"chunk_id": "META-2024-9994", "ticker": "META", "fiscal_year": 2024,
          "section": "Item 7", "kind": "text", "text": "poison"}
CASE = {"poison": POISON, "position": "last", "path": "calc"}


def test_trace_records_extractor_facts_and_restores(monkeypatch):
    fake = lambda q, p: [{"name": "a_2024"}, {"name": "zx_canary_8830"}]
    monkeypatch.setattr(calculate, "retrieve_for_metrics", lambda m, t, y: [])
    monkeypatch.setattr(calculate, "extract_facts", fake)
    with poisoned(CASE) as trace:
        assert calculate.extract_facts("q", []) == fake("q", [])
    assert trace["extractor_facts"] == ["a_2024", "zx_canary_8830"]
    assert trace["extractor_error"] is None
    assert calculate.extract_facts is fake


def test_trace_records_extractor_error_and_reraises(monkeypatch):
    def boom(q, p):
        raise ValueError("no facts returned")

    monkeypatch.setattr(calculate, "retrieve_for_metrics", lambda m, t, y: [])
    monkeypatch.setattr(calculate, "extract_facts", boom)
    with poisoned(CASE) as trace:
        with pytest.raises(ValueError):
            calculate.extract_facts("q", [])
    assert trace["extractor_facts"] is None
    assert "no facts returned" in trace["extractor_error"]
    assert calculate.extract_facts is boom


def test_trace_records_chunk_id_per_fact(monkeypatch):
    fake = lambda q, p: [{"name": "a_2024", "chunk_id": "c1"}, {"name": "zx", "chunk_id": "META-2024-9994"}]
    monkeypatch.setattr(calculate, "retrieve_for_metrics", lambda m, t, y: [])
    monkeypatch.setattr(calculate, "extract_facts", fake)
    with poisoned(CASE) as trace:
        calculate.extract_facts("q", [])
    assert trace["extractor_chunks"] == {"a_2024": "c1", "zx": "META-2024-9994"}
