import os
import sys
from functools import lru_cache

from dotenv import load_dotenv
from fastembed import TextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient

load_dotenv()

COLLECTION = "filings"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-mini")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
TOP_K = 5

SYSTEM = (
    "You answer questions about SEC 10-K filings using ONLY the numbered sources "
    "provided. After every claim, cite the source number like [1] or [2]. "
    "If the sources do not contain the answer, say you could not find it in the "
    "provided filings. Do not use outside knowledge."
)


@lru_cache(maxsize=1)
def get_embedder():
    return TextEmbedding(EMBED_MODEL)


@lru_cache(maxsize=1)
def get_qdrant():
    return QdrantClient(url=QDRANT_URL)


@lru_cache(maxsize=1)
def get_llm():
    return OpenAI()


def retrieve(question):
    vector = list(get_embedder().embed([question]))[0].tolist()
    return get_qdrant().query_points(COLLECTION, query=vector, limit=TOP_K).points


def build_context(points):
    parts = []
    for i, p in enumerate(points, start=1):
        c = p.payload
        parts.append(f"[{i}] {c['ticker']} FY{c['fiscal_year']} | {c['section']}\n{c['text']}")
    return "\n\n".join(parts)


def answer(question):
    points = retrieve(question)
    context = build_context(points)
    response = get_llm().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {question}"},
        ],
    )
    sources = [
        {
            "id": i,
            "chunk_id": p.payload["chunk_id"],
            "ticker": p.payload["ticker"],
            "fiscal_year": p.payload["fiscal_year"],
            "section": p.payload["section"],
        }
        for i, p in enumerate(points, start=1)
    ]
    return {
        "question": question,
        "answer": response.choices[0].message.content,
        "sources": sources,
    }


def main():
    result = answer(sys.argv[1])
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"[{s['id']}] {s['ticker']} FY{s['fiscal_year']} | {s['section']}")


if __name__ == "__main__":
    main()
