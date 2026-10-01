import json

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION = "filings"
MODEL = "BAAI/bge-small-en-v1.5"
CHUNKS_PATH = "data/processed/chunks.jsonl"
BATCH = 128


def main():
    with open(CHUNKS_PATH) as f:
        chunks = [json.loads(line) for line in f]

    client = QdrantClient(url="http://localhost:6333")
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    model = TextEmbedding(MODEL)
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        vectors = list(model.embed([c["text"] for c in batch]))
        points = [
            PointStruct(id=start + i, vector=v.tolist(), payload=c)
            for i, (c, v) in enumerate(zip(batch, vectors))
        ]
        client.upsert(COLLECTION, points=points)
        print(f"{start + len(batch)}/{len(chunks)}")

    print("done:", client.count(COLLECTION).count)


if __name__ == "__main__":
    main()
