import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ledgerlens.agent import run  # noqa: E402
from ledgerlens.injection import label_case  # noqa: E402
from ledgerlens.injection_harness import poisoned  # noqa: E402


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def one_line(text, n=160):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + "..."


def load_cases(path, split):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return [r for r in rows if r.get("split") == split]


def calc_summary(calc):
    if not calc:
        return "calculation: none"
    if calc.get("ok"):
        names = [f.get("name") for f in calc.get("facts", []) if isinstance(f, dict)]
        return f"calculation: ok result={calc.get('result')} facts={names}"
    return f"calculation: not ok error={one_line(str(calc.get('error')), 120)}"


def extractor_summary(trace, canary):
    if not trace:
        return "extractor: no trace"
    if trace.get("extractor_error"):
        return f"extractor: error {one_line(trace['extractor_error'], 120)}"
    names = trace.get("extractor_facts")
    if names is None:
        return "extractor: not called"
    returned = (canary in names) if canary else "n/a"
    return f"extractor: facts={names} canary_returned={returned}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out")
    args = ap.parse_args()

    cases = load_cases(ROOT / "eval" / "injection.jsonl", args.split)
    if not cases:
        sys.exit(f"no cases for split {args.split!r}")

    lines, counts = [], Counter()
    for c in cases:
        route, answer, calc, trace = "-", "", None, None
        try:
            with poisoned(c) as trace:
                out = run(c["question"])
            route = out.get("route", "-")
            answer = out.get("answer", "")
            calc = out.get("calculation")
            result = label_case(c, out)
        except Exception as exc:  # a crash is its own label, the run goes on
            result = {"label": "CRASH", "utility": False}
            answer = f"{type(exc).__name__}: {exc}"
        counts[result["label"]] += 1
        lines.append(
            f"{result['label']} {c['id']} [{c['category']}] path={c['path']} "
            f"position={c['position']} route={route} utility={result['utility']}"
        )
        lines.append(f"     answer: {one_line(answer)}")
        if c["path"] == "calc":
            lines.append(f"     {calc_summary(calc)}")
            lines.append(f"     {extractor_summary(trace, c.get('canary'))}")

    commit = git("rev-parse", "--short", "HEAD")
    dirty = any(not l.startswith("??") for l in git("status", "--porcelain").splitlines())
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    lines += ["", f"labels: {summary} (split {args.split}, {len(cases)} cases)"]
    lines.append(f"code commit {commit}" + (" (uncommitted changes present)" if dirty else ""))
    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")


if __name__ == "__main__":
    main()
