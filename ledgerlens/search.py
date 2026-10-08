import json
import os
import re
import sys
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

COLLECTION = "filings"
MODEL = "BAAI/bge-small-en-v1.5"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
CHUNKS_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "chunks.jsonl"

# Hybrid settings, picked on the dev split (see eval/ results)
RRF_K = 60
W_DENSE = 1.0
W_BM25 = 3.0
CANDIDATES = 100

_model = None
_client = None
_chunks = None
_by_id = None
_bm25_cache = {}


def build_filter(ticker=None, fiscal_year=None):
    """Build a Qdrant filter from optional ticker / fiscal_year (None = no filter)."""
    conditions = []
    if ticker is not None:
        conditions.append(FieldCondition(key="ticker", match=MatchValue(value=ticker)))
    if fiscal_year is not None:
        conditions.append(FieldCondition(key="fiscal_year", match=MatchValue(value=int(fiscal_year))))
    return Filter(must=conditions) if conditions else None


def tokenize(text):
    return re.findall(r"[a-z0-9]+(?:[.,][0-9]+)*", text.lower())


def _load_chunks():
    global _chunks, _by_id
    if _chunks is None:
        with open(CHUNKS_PATH) as f:
            _chunks = [json.loads(line) for line in f if line.strip()]
        _by_id = {c["chunk_id"]: c for c in _chunks}
    return _chunks


def _bm25_index(ticker, fiscal_year):
    key = (ticker, fiscal_year)
    if key not in _bm25_cache:
        from rank_bm25 import BM25Okapi  # imported here so dense-only use needs no extra package

        pool = [
            c for c in _load_chunks()
            if (ticker is None or c["ticker"] == ticker)
            and (fiscal_year is None or int(c["fiscal_year"]) == int(fiscal_year))
        ]
        bm = BM25Okapi([tokenize(c["text"]) for c in pool]) if pool else None
        _bm25_cache[key] = (pool, bm)
    return _bm25_cache[key]


def _dense(question, limit, ticker, fiscal_year):
    global _model, _client
    if _model is None:
        _model = TextEmbedding(MODEL)
        _client = QdrantClient(url=QDRANT_URL)
    vector = list(_model.embed([question]))[0].tolist()
    qfilter = build_filter(ticker, fiscal_year)
    result = _client.query_points(COLLECTION, query=vector, limit=limit, query_filter=qfilter)
    return [(p.score, p.payload) for p in result.points]


def rrf_fuse(rankings, weights, k=RRF_K):
    """rankings = lists of chunk_ids (best first). Returns [(score, chunk_id)] best first."""
    scores = {}
    for ids, w in zip(rankings, weights):
        for rank, cid in enumerate(ids, start=1):
            scores[cid] = scores.get(cid, 0.0) + w / (k + rank)
    return sorted(((s, cid) for cid, s in scores.items()), reverse=True)


def search(question, limit=3, ticker=None, fiscal_year=None, mode="dense"):
    """Return a list of (score, payload) for the top chunks. mode: 'dense' or 'hybrid'."""
    if mode == "dense":
        return _dense(question, limit, ticker, fiscal_year)
    if mode != "hybrid":
        raise ValueError(f"unknown mode: {mode}")
    pool, bm = _bm25_index(ticker, fiscal_year)
    if not pool:
        return []  # no chunks for this ticker/year, nothing to rank
    dense = _dense(question, CANDIDATES, ticker, fiscal_year)
    dense_ids = [p["chunk_id"] for _, p in dense]
    scores = bm.get_scores(tokenize(question))
    top = sorted(range(len(pool)), key=lambda i: -scores[i])[:CANDIDATES]
    bm_ids = [pool[i]["chunk_id"] for i in top]
    fused = rrf_fuse([dense_ids, bm_ids], [W_DENSE, W_BM25])
    _load_chunks()
    return [(s, _by_id[cid]) for s, cid in fused[:limit]]


def main():
    question = sys.argv[1]
    for score, c in search(question):
        print(f"\nscore={score:.3f} | {c['ticker']} FY{c['fiscal_year']} | {c['section']}")
        print(c["text"][:200].replace("\n", " "))


if __name__ == "__main__":
    main()
