"""Run the calculation agent on eval/calc_golden.jsonl and score it.

Usage: python eval/calc_eval.py --split dev [--out eval/calc_dev.txt]
Each question costs 4 OpenAI calls (router, planner, extract, formula).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

GOLDEN = Path(__file__).resolve().parent / "calc_golden.jsonl"


def load_rows(split):
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    return rows if split == "all" else [r for r in rows if r["split"] == split]


def score(row, out):
    """Return (passed, detail) for one agent output dict."""
    if out.get("route") != "calculate":
        return False, f"routed to {out.get('route')}"
    calc = out.get("calculation") or {}
    if not calc.get("ok"):
        return False, f"not verified: {calc.get('error')}"
    result = calc.get("result")
    if not isinstance(result, (int, float)):
        return False, f"no numeric result: {result!r}"
    if abs(result - row["expected"]) <= row["tolerance"]:
        return True, f"result {result:.4f}"
    return False, f"result {result:.4f}, wanted {row['expected']}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="dev", help="dev, test, test2 or all")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    from ledgerlens.agent import run

    rows = load_rows(args.split)
    lines = []
    passed = 0
    for row in rows:
        try:
            out = run(row["question"])
            ok, detail = score(row, out)
        except Exception as e:  # keep going, but show what crashed
            ok, detail = False, f"CRASH {type(e).__name__}: {e}"
        passed += ok
        lines.append(f"{'PASS' if ok else 'FAIL'} {row['id']} {row['ticker']} | {detail}")
        print(lines[-1], flush=True)
    summary = f"split={args.split} passed {passed}/{len(rows)}"
    lines.append(summary)
    print(summary)
    if args.out:
        Path(args.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
