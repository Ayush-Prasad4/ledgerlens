import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GOLDEN = ROOT / "eval" / "golden.jsonl"
K = 5


def keywords(entry):
    kw = entry["must_contain"]
    return [kw] if isinstance(kw, str) else kw


def is_hit(entry, payload):
    if payload["ticker"] != entry["ticker"]:
        return False
    if int(payload["fiscal_year"]) != entry["fiscal_year"]:
        return False
    text = payload["text"].lower()
    return any(k.lower() in text for k in keywords(entry))


def load_golden():
    lines = GOLDEN.read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def evaluate(entries, k=K):
    # imported here so tests can import this file without needing Qdrant
    from ledgerlens.search import search

    rows = []
    for e in entries:
        results = search(e["question"], limit=k)
        rank = None
        for i, (score, payload) in enumerate(results, start=1):
            if is_hit(e, payload):
                rank = i
                break
        rows.append((e["id"], rank, results[0][1]))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=float, default=None,
                        help="exit with code 1 if hit-rate@5 is below this, e.g. 0.63")
    args = parser.parse_args()

    rows = evaluate(load_golden())
    for qid, rank, top in rows:
        if rank:
            print(f"{qid} HIT  (rank {rank})")
        else:
            print(f"{qid} MISS (top-1 was {top['ticker']} FY{top['fiscal_year']} | {top['section']})")

    n = len(rows)
    hit5 = sum(1 for _, r, _ in rows if r)
    hit1 = sum(1 for _, r, _ in rows if r == 1)
    print(f"\nhit-rate@{K}: {hit5}/{n} = {hit5 / n:.0%}")
    print(f"hit-rate@1: {hit1}/{n} = {hit1 / n:.0%}")

    if args.min is not None:
        if hit5 / n < args.min:
            print(f"GATE FAILED: {hit5 / n:.2f} is below the minimum {args.min:.2f}")
            sys.exit(1)
        print("GATE OK")


if __name__ == "__main__":
    main()
