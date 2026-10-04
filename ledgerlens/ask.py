import os
import sys
from functools import lru_cache

from dotenv import load_dotenv
from fastembed import TextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient

from ledgerlens.query_parser import parse_query, parse_years
from ledgerlens.search import search

load_dotenv()

COLLECTION = "filings"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-mini")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
TOP_K = 5
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "hybrid")

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
    ticker, year = parse_query(question)
    years = parse_years(question)
    if ticker and len(years) > 1:
        # one search per fiscal year, so every year's chunks reach the LLM
        points = []
        for y in years:
            hits = search(question, limit=TOP_K, ticker=ticker, fiscal_year=y, mode=RETRIEVAL_MODE)
            points.extend(payload for _score, payload in hits)
        return points
    hits = search(question, limit=TOP_K, ticker=ticker, fiscal_year=year, mode=RETRIEVAL_MODE)
    if not hits and ticker and year:
        # no filing for that year: a later 10-K carries it as a comparative column
        for later in (year + 1, year + 2):
            hits = search(question, limit=TOP_K, ticker=ticker, fiscal_year=later, mode=RETRIEVAL_MODE)
            if hits:
                break
    return [payload for _score, payload in hits]


def build_context(points):
    parts = []
    for i, p in enumerate(points, start=1):
        c = p
        parts.append(f"[{i}] {c['ticker']} FY{c['fiscal_year']} | {c['section']}\n{c['text']}")
    return "\n\n".join(parts)


NOT_FOUND = "I could not find this in the provided filings."


def generate(question, points):
    if not points:
        # nothing retrieved: do not ask the LLM, answer deterministically
        return {"question": question, "answer": NOT_FOUND, "sources": []}
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
            "chunk_id": p["chunk_id"],
            "ticker": p["ticker"],
            "fiscal_year": p["fiscal_year"],
            "section": p["section"],
        }
        for i, p in enumerate(points, start=1)
    ]
    return {
        "question": question,
        "answer": response.choices[0].message.content,
        "sources": sources,
    }


def answer(question):
    return generate(question, retrieve(question))


def main():
    result = answer(sys.argv[1])
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"[{s['id']}] {s['ticker']} FY{s['fiscal_year']} | {s['section']}")


if __name__ == "__main__":
    main()
