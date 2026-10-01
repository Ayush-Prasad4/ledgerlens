from __future__ import annotations

import json
import random
import sys

from ledgerlens.config import RAW_DIR

CHUNKS_PATH = RAW_DIR.parent / "processed" / "chunks.jsonl"


def load_chunks() -> list[dict]:
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def show_stats(chunks: list[dict]) -> None:
    print(f"Total chunks: {len(chunks)}")

    for kind in ("text", "table"):
        sizes = [len(c["text"]) for c in chunks if c["kind"] == kind]

        if sizes:
            average = sum(sizes) // len(sizes)
            print(
                f"{kind}: {len(sizes)} chunks, "
                f"min {min(sizes)}, avg {average}, max {max(sizes)} characters"
            )

    tiny = [c for c in chunks if len(c["text"]) < 150]
    print(f"Bahut chhote chunks (150 characters se kam): {len(tiny)}")


def show_sample(chunks: list[dict], kind: str, count: int, seed: int) -> None:
    pool = [c for c in chunks if c["kind"] == kind]
    random.seed(seed)

    for chunk in random.sample(pool, min(count, len(pool))):
        print("=" * 80)
        print(chunk["chunk_id"], "|", chunk["kind"], "|", len(chunk["text"]), "characters")
        print(chunk["text"])


def main() -> None:
    chunks = load_chunks()
    mode = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if mode == "stats":
        show_stats(chunks)
    elif mode in ("text", "table"):
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        show_sample(chunks, mode, count, seed)
    else:
        print("Use: stats | text [N] [seed] | table [N] [seed]")


if __name__ == "__main__":
    main()
