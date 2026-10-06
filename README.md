# LedgerLens

**A financial-filings agent that refuses to guess numbers.** Ask questions about 10-K filings of large US tech companies. Answers cite their sources, and every number used in a calculation is checked against the filing text in code before the calculator may touch it. If it cannot verify, it says so.

Built solo, evaluation-first: dev splits for tuning, sealed test splits run once.

## Highlights

- **Verified arithmetic.** Each number in a growth rate or ratio must appear inside an exact quote of the cited chunk, and the check runs in plain code, not in the LLM. One failed check rejects the whole calculation.
- **Sealed test results.** On calculation questions written before the run: 7 of 8 correct, and the one miss was a safe failure ("could not verify"), not a wrong number.
- **A real bug found by the eval.** On a dev question the agent returned 27,703 instead of 33,147 because a bracketed loss, $(2,722), lost its negative sign and still passed verification. Fixed in the prompt and the checker, with tests. Details under Results.
- **Honest retrieval numbers.** An automatic ticker/year filter raised test hit@1 from 3/10 to 5/10. Hybrid search and a cross-encoder reranker did not show a clear gain on test, and the reranker was dropped.
- **Security:** a red-team harness based on the OWASP LLM Top 10 is in progress (see Status).

**Stack:** Python 3.12, FastAPI, LangGraph, Qdrant, BM25 + dense retrieval, OpenAI gpt-5-mini, pytest, GitHub Actions.

## How it works

    question
       |
       v
    router (LLM, falls back to "lookup" on bad output)
       |
       +-- lookup ----> retrieve (hybrid: dense + BM25, ticker/year filter)
       |                   |
       |                   v
       |                generate answer with citations
       |
       +-- calculate --> planner (LLM: which metrics are needed)
                            |
                            v
                         retrieve per metric and per year
                            |
                            v
                         extract facts (LLM: name, value, exact quote, chunk id)
                            |
                            v
                         verify facts in code (quote must be inside the chunk,
                         value must be inside the quote, negatives need brackets,
                         one failure rejects the whole list)
                            |
                            v
                         formula writer (LLM: expression over fact names only)
                            |
                            v
                         safe calculator (ast-based, + - * / only)
                            |
                            v
                         answer with result, formula and sources

If any step cannot be verified, the answer says so instead of guessing.

## Status

| Stage | What | State |
|---|---|---|
| 0-5 | Data pipeline, retrieval, cited answers, API | done |
| 6 | Evaluation set and metrics | done |
| 7 | Filter and hybrid search | done |
| 8 | Agent: router, verified facts, safe calculator | done |
| 9 | Red-team harness (OWASP LLM Top 10) | in progress: dev cases written and run, sealed test not yet run |
| 10 | AWS, Terraform, CI deploy | not started |
| 11 | UI, demo | not started |

## Results

Dev numbers are tuned (the code was developed on them). Test numbers come from sealed questions written before the run.

### Retrieval (Stage 7), hit@5 / hit@1

| Config | Dev (13 q) | Test (10 q, run once) |
|---|---|---|
| Baseline: dense, no filter | 8/13, 6/13 | 6/10, 3/10 |
| Dense + auto filter | 9/13, 7/13 | 6/10, 5/10 |
| Hybrid + auto filter | 11/13, 8/13 | 7/10, 4/10 |

The auto filter is the clearest gain. The hybrid gain on test is within noise (one question = 10 points). A cross-encoder reranker was tried and dropped. Details: eval/stage7_summary.md.

### Calculation questions (Stage 8), result within 0.01 of the filing-derived value

| Split | Passed | Note |
|---|---|---|
| Dev c01-c06 | 6/6 | tuned: a sign bug on bracketed losses was found and fixed on this set |
| Test t01-t05 | 4/5 | the miss was a safe failure ("no facts returned"), not a wrong number |
| Test t06-t08 (new questions) | 3/3 | only 3 questions |

Files: eval/calc_dev.txt, eval/calc_test.txt, eval/calc_test2.txt.

## Known limitations

Data
- 14 filings only: AAPL FY2023-25, AMZN FY2023-25, GOOGL FY2023-25, META FY2024-25, MSFT FY2024-26 (4,298 chunks). Questions about other companies or years are not covered.
- Item 6 is missing for AMZN, META and MSFT, and is only a "[Reserved]" stub for AAPL and GOOGL. META FY2024 has no separate Item 10. 61 of 4,298 chunks are under 100 characters.

Evaluation
- The golden set is small (23 retrieval questions, 10 of them test; 8 calculation test questions). One retrieval test question is 10 points.
- Golden questions were written with keywords checked in the text, so lexical search (BM25) may be favoured.
- "Oracle filter" rows use the true ticker and year from the golden set. They are an upper bound, not a real result.
- The query parser was fixed after the Stage 7 test run (a bare year like "in 2024" gave no year). The Stage 7 test numbers were recorded before that fix and were not rerun.
- Dev numbers are tuned. Only test numbers should be quoted as results.

Calculation path
- One company per question. Multi-company comparisons are not supported.
- The checker verifies that a number appears in the quoted row, but not which year column it belongs to. A row such as "391,035 | 383,285 | 394,328" with swapped columns would pass. Three-column rows from both newest-first and oldest-first tables gave correct results in the checks done so far, but that is not an eval.
- Units are not tracked. A result ending in "* 100" is labelled with %, other results are shown as a bare number, and the answer asks the reader to check the filing for the unit.
- A calculation that cannot be verified fails with a message instead of an answer (this happened on test question t05).

Deployment
- Hybrid search needs data/processed/chunks.jsonl at runtime for BM25. The Docker image has not been rebuilt since the agent was added; until chunks.jsonl is shipped in the image (or BM25 moves to Qdrant sparse vectors) the container has to run with RETRIEVAL_MODE=dense.
- CI runs the unit tests only. The eval score gates need Qdrant and the filings, so they run locally.
