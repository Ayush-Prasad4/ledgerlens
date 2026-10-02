import json
import sys

kw = sys.argv[1].lower()
ticker = sys.argv[2].upper() if len(sys.argv) > 2 else None

hits = []
with open("data/processed/chunks.jsonl") as f:
    for line in f:
        c = json.loads(line)
        if ticker and c["ticker"] != ticker:
            continue
        i = c["text"].lower().find(kw)
        if i >= 0:
            hits.append((c, i))

print(len(hits), "chunks match")
for c, i in hits[:8]:
    t = c["text"]
    snippet = t[max(0, i - 60): i + 100].replace("\n", " ")
    print(c["chunk_id"], "|", c["section"], "|", snippet)
