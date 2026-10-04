from ledgerlens import search as search_mod

FAKE = [
    {"chunk_id": "META-2024-0001", "ticker": "META", "fiscal_year": 2024, "text": "total revenue"},
]


def _use_fake_chunks(monkeypatch):
    monkeypatch.setattr(search_mod, "_load_chunks", lambda: FAKE)
    monkeypatch.setattr(search_mod, "_bm25_cache", {})


def test_bm25_index_empty_pool_does_not_crash(monkeypatch):
    _use_fake_chunks(monkeypatch)
    pool, bm = search_mod._bm25_index("META", 2023)
    assert pool == []
    assert bm is None


def test_hybrid_search_with_no_chunks_returns_empty(monkeypatch):
    _use_fake_chunks(monkeypatch)
    result = search_mod.search("total revenue", ticker="META", fiscal_year=2023, mode="hybrid")
    assert result == []
