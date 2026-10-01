import sys

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

COLLECTION = "filings"
MODEL = "BAAI/bge-small-en-v1.5"


def main():
    question = sys.argv[1]
    model = TextEmbedding(MODEL)
    vector = list(model.embed([question]))[0].tolist()

    client = QdrantClient(url="http://localhost:6333")
    result = client.query_points(COLLECTION, query=vector, limit=3)

    for p in result.points:
        c = p.payload
        print(f"\nscore={p.score:.3f} | {c['ticker']} FY{c['fiscal_year']} | {c['section']}")
        print(c["text"][:200].replace("\n", " "))


if __name__ == "__main__":
    main()
