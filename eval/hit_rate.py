import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ledgerlens.search import search  # noqa: E402

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


def main():
    lines = GOLDEN.read_text().splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    hits = 0
    for e in entries:
        results = search(e["question"], limit=K)
        rank = None
        for i, (score, payload) in enumerate(results, start=1):
            if is_hit(e, payload):
                rank = i
                break
        if rank:
            hits += 1
            print(f"{e['id']} HIT  (rank {rank})")
        else:
            top = results[0][1]
            print(f"{e['id']} MISS (top-1 was {top['ticker']} FY{top['fiscal_year']} | {top['section']})")
    print(f"\nhit-rate@{K}: {hits}/{len(entries)} = {hits / len(entries):.0%}")


if __name__ == "__main__":
    main()
