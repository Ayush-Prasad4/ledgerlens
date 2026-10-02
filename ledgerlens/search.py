import sys

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

COLLECTION = "filings"
MODEL = "BAAI/bge-small-en-v1.5"

_model = None
_client = None


def search(question, limit=3):
    """Return a list of (score, payload) for the top chunks."""
    global _model, _client
    if _model is None:
        _model = TextEmbedding(MODEL)
        _client = QdrantClient(url="http://localhost:6333")
    vector = list(_model.embed([question]))[0].tolist()
    result = _client.query_points(COLLECTION, query=vector, limit=limit)
    return [(p.score, p.payload) for p in result.points]


def main():
    question = sys.argv[1]
    for score, c in search(question):
        print(f"\nscore={score:.3f} | {c['ticker']} FY{c['fiscal_year']} | {c['section']}")
        print(c["text"][:200].replace("\n", " "))


if __name__ == "__main__":
    main()
