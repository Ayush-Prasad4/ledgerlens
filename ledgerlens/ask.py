import os
import sys

from dotenv import load_dotenv
from fastembed import TextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient

load_dotenv()

COLLECTION = "filings"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-mini")
TOP_K = 5

SYSTEM = (
    "You answer questions about SEC 10-K filings using ONLY the numbered sources "
    "provided. After every claim, cite the source number like [1] or [2]. "
    "If the sources do not contain the answer, say you could not find it in the "
    "provided filings. Do not use outside knowledge."
)


def retrieve(question):
    model = TextEmbedding(EMBED_MODEL)
    vector = list(model.embed([question]))[0].tolist()
    client = QdrantClient(url="http://localhost:6333")
    return client.query_points(COLLECTION, query=vector, limit=TOP_K).points


def build_context(points):
    parts = []
    for i, p in enumerate(points, start=1):
        c = p.payload
        parts.append(f"[{i}] {c['ticker']} FY{c['fiscal_year']} | {c['section']}\n{c['text']}")
    return "\n\n".join(parts)


def main():
    question = sys.argv[1]
    points = retrieve(question)
    context = build_context(points)

    response = OpenAI().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {question}"},
        ],
    )

    print(response.choices[0].message.content)
    print("\nSources:")
    for i, p in enumerate(points, start=1):
        c = p.payload
        print(f"[{i}] {c['ticker']} FY{c['fiscal_year']} | {c['section']}")


if __name__ == "__main__":
    main()
