import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ledgerlens import ask  # noqa: E402

# name -> function(question) -> list of chunk payload dicts, best first
STRATEGIES = {"current": ask.retrieve}


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
    lines, h5, h1 = [], 0, 0
    for r in rows:
        pts = retrieve(r["question"])
        hits = [is_hit(r, p) for p in pts]
        a5 = any(hits[:5])
        a1 = bool(hits and hits[0])
        h5 += a5
        h1 += a1
        first = next((i + 1 for i, h in enumerate(hits) if h), None)
        lines.append(f"{r['id']} hit@5={'Y' if a5 else 'N'} hit@1={'Y' if a1 else 'N'} first_hit_rank={first} chunks={len(pts)}")

    commit = git("rev-parse", "--short", "HEAD")
    dirty = any(not l.startswith("??") for l in git("status", "--porcelain").splitlines())
    lines += ["", f"strategy {args.strategy}, split {args.split}: hit@5 {h5}/{len(rows)}, hit@1 {h1}/{len(rows)}"]
    lines.append(f"code commit {commit}" + (" (uncommitted changes present)" if dirty else ""))
    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")


if __name__ == "__main__":
    main()
