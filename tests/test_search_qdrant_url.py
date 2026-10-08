from ledgerlens import search


class FakeVector:
    def tolist(self):
        return [0.0]


class FakeModel:
    def __init__(self, *args, **kwargs):
        pass

    def embed(self, texts):
        return [FakeVector() for _ in texts]


class FakeResult:
    points = []


def test_dense_uses_qdrant_url(monkeypatch):
    seen = {}

    class FakeClient:
        def __init__(self, url):
            seen["url"] = url

        def query_points(self, *args, **kwargs):
            return FakeResult()

    monkeypatch.setattr(search, "TextEmbedding", FakeModel)
    monkeypatch.setattr(search, "QdrantClient", FakeClient)
    monkeypatch.setattr(search, "QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setattr(search, "build_filter", lambda ticker, fiscal_year: None)
    monkeypatch.setattr(search, "_model", None)
    monkeypatch.setattr(search, "_client", None)

    assert search._dense("q", 3, None, None) == []
    assert seen["url"] == "http://qdrant:6333"
