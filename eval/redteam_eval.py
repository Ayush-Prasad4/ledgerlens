import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ledgerlens.agent import run  # noqa: E402
from ledgerlens.redteam import check_answer, load_cases  # noqa: E402


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def one_line(text, n=160):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + "..."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out")
    args = ap.parse_args()

    cases = load_cases(ROOT / "eval" / "redteam.jsonl", args.split)
    if not cases:
        sys.exit(f"no cases for split {args.split!r}")

    lines, passed = [], 0
    for c in cases:
        route = "-"
        try:
            out = run(c["question"])
            route = out.get("route", "-")
            answer = out.get("answer", "")
            ok, reason = check_answer(c, answer)
        except Exception as exc:  # a crash counts as a failure, the run goes on
            answer = ""
            ok, reason = False, f"CRASH {type(exc).__name__}: {exc}"
        passed += ok
        lines.append(f"{'PASS' if ok else 'FAIL'} {c['id']} [{c['category']}] route={route} {reason}")
        lines.append(f"     answer: {one_line(answer)}")

    commit = git("rev-parse", "--short", "HEAD")
    dirty = any(not l.startswith("??") for l in git("status", "--porcelain").splitlines())
    lines += ["", f"passed {passed}/{len(cases)} (split {args.split})"]
    lines.append(f"code commit {commit}" + (" (uncommitted changes present)" if dirty else ""))
    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")


if __name__ == "__main__":
    main()
