import sys

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

COLLECTION = "filings"
MODEL = "BAAI/bge-small-en-v1.5"

_model = None
_client = None


def build_filter(ticker=None, fiscal_year=None):
    """Build a Qdrant filter from optional ticker / fiscal_year (None = no filter)."""
    conditions = []
    if ticker is not None:
        conditions.append(FieldCondition(key="ticker", match=MatchValue(value=ticker)))
    if fiscal_year is not None:
        conditions.append(FieldCondition(key="fiscal_year", match=MatchValue(value=int(fiscal_year))))
    return Filter(must=conditions) if conditions else None


def search(question, limit=3, ticker=None, fiscal_year=None):
    """Return a list of (score, payload) for the top chunks."""
    global _model, _client
    if _model is None:
        _model = TextEmbedding(MODEL)
        _client = QdrantClient(url="http://localhost:6333")
    vector = list(_model.embed([question]))[0].tolist()
    qfilter = build_filter(ticker, fiscal_year)
    result = _client.query_points(COLLECTION, query=vector, limit=limit, query_filter=qfilter)
    return [(p.score, p.payload) for p in result.points]


def main():
    question = sys.argv[1]
    for score, c in search(question):
        print(f"\nscore={score:.3f} | {c['ticker']} FY{c['fiscal_year']} | {c['section']}")
        print(c["text"][:200].replace("\n", " "))


if __name__ == "__main__":
    main()
