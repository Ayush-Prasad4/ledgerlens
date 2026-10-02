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


def load_golden(split=None):
    lines = GOLDEN.read_text().splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    if split in (None, "all"):
        return entries
    return [e for e in entries if e.get("split") == split]


def evaluate(entries, k=K, use_filter=False):
    # imported here so tests can import this file without needing Qdrant
    from ledgerlens.search import search

    rows = []
    for e in entries:
        if use_filter:
            results = search(e["question"], limit=k,
                             ticker=e["ticker"], fiscal_year=e["fiscal_year"])
        else:
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
    parser.add_argument("--split", choices=["dev", "test", "all"], default="all",
                        help="which golden questions to run (default: all)")
    parser.add_argument("--filter", choices=["none", "oracle"], default="none",
                        help="oracle = filter by the golden ticker+fiscal_year (upper bound)")
    args = parser.parse_args()

    entries = load_golden(args.split)
    if not entries:
        print(f"No questions found for split '{args.split}'")
        sys.exit(1)

    rows = evaluate(entries, use_filter=(args.filter == "oracle"))
    print(f"split: {args.split} | filter: {args.filter}")
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
