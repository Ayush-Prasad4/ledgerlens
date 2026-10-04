import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ledgerlens import ask  # noqa: E402
from ledgerlens.lookup_retrieval import retrieve_lookup  # noqa: E402
from ledgerlens.query_parser import parse_query  # noqa: E402
from ledgerlens.search import search  # noqa: E402


def current8(question):
    """Same as ask.retrieve for a single-year question, but 8 chunks (equal budget to merged)."""
    ticker, year = parse_query(question)
    hits = search(question, limit=8, ticker=ticker, fiscal_year=year, mode=ask.RETRIEVAL_MODE)
    return [payload for _score, payload in hits]


# name -> function(question) -> list of chunk payload dicts, best first
STRATEGIES = {"current": ask.retrieve, "current8": current8, "merged": retrieve_lookup}


def keywords(row):
    m = row["must_contain"]
    return [m] if isinstance(m, str) else list(m)


def is_hit(row, p):
    if p["ticker"] != row["ticker"] or int(p["fiscal_year"]) != int(row["fiscal_year"]):
        return False
    text = p["text"].lower()
    return any(k.lower() in text for k in keywords(row))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="current", choices=sorted(STRATEGIES))
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.split != "dev":
        print("warning: only the dev split is for tuning; test is sealed", file=sys.stderr)

    path = ROOT / "eval" / "golden.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if args.split != "all":
        rows = [r for r in rows if r["split"] == args.split]

    retrieve = STRATEGIES[args.strategy]
    lines, h5, h1, hall = [], 0, 0, 0
    for r in rows:
        pts = retrieve(r["question"])
        hits = [is_hit(r, p) for p in pts]
        a5, a1, aall = any(hits[:5]), bool(hits and hits[0]), any(hits)
        h5 += a5
        h1 += a1
        hall += aall
        first = next((i + 1 for i, h in enumerate(hits) if h), None)
        yn = lambda b: "Y" if b else "N"
        lines.append(f"{r['id']} hit@5={yn(a5)} hit@1={yn(a1)} hit@all={yn(aall)} first_hit_rank={first} chunks={len(pts)}")

    commit = git("rev-parse", "--short", "HEAD")
    dirty = any(not l.startswith("??") for l in git("status", "--porcelain").splitlines())
    n = len(rows)
    lines += ["", f"strategy {args.strategy}, split {args.split}: hit@5 {h5}/{n}, hit@1 {h1}/{n}, hit@all {hall}/{n} (all = every retrieved chunk)"]
    lines.append(f"code commit {commit}" + (" (uncommitted changes present)" if dirty else ""))
    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")


if __name__ == "__main__":
    main()
