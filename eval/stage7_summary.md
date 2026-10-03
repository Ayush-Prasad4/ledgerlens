# Stage 7 results: filter and hybrid search

hit@5 / hit@1 (retrieved chunk must match ticker + fiscal year + keyword).

| Config | Dev (13 q) | Test (10 q, run once) |
|---|---|---|
| Baseline: dense, no filter | 8/13, 6/13 | 6/10, 3/10 |
| Dense + auto filter | 9/13, 7/13 | 6/10, 5/10 |
| Hybrid + auto filter | 11/13, 8/13 | 7/10, 4/10 |
| Dense + oracle filter (upper bound) | 9/13, 7/13 | not run |
| Hybrid + oracle filter (upper bound) | 11/13, 8/13 | not run |

## Reading the numbers
- The auto filter is the clearest gain: test hit@1 went from 3/10 to 5/10.
- Hybrid gain on test is within noise: +1 question on hit@5, -1 question on hit@1 vs dense + auto. One question = 10 percentage points.
- Dev numbers are tuned (weights and parser were developed on dev), so test numbers are the honest ones.
- On the 6 original test questions hybrid + auto got 6/6 vs 4/6 for dense + auto; on the 4 paraphrased questions (q20-q23) hybrid got 1/4 vs 2/4. Suggests BM25 has a lexical advantage when questions share words with the text. Sample is tiny.
- q22 and q23 missed in every config. q22 hybrid top-1 was AMZN FY2023, probably because the parser did not extract a year from "in 2024" (not verified). Not fixed after the test run, by design.

## Tried and dropped
- Cross-encoder reranker (MiniLM-L-6 and L-12) over hybrid top-20: no clear net gain on dev, slower (0.5-0.9 s/query), dropped.

## Known limitations
- Golden set is small (23 questions); test split only 10.
- Golden questions written with keywords checked in the text, so lexical search may be favoured.
- Oracle filter = true ticker and year from the golden set; an upper bound, not a real result.
- Hybrid needs data/processed/chunks.jsonl at runtime (BM25); must be shipped in the Docker image or moved to Qdrant sparse vectors at deploy time.
