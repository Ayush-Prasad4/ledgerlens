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

## Example

A lookup question, answered with citations:

    $ python -m ledgerlens.agent "What were Apple's total net sales in fiscal 2024?"
    Route: lookup

    Apple’s total net sales in fiscal 2024 were $391,035 million [1][6].

    Sources:
    [1] AAPL FY2024 | Item 8. Financial Statements and Supplementary Data
    [2] AAPL FY2024 | Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
    ... (8 sources in total, all AAPL FY2024)

A calculation question. The numbers below passed the in-code check (quote inside the chunk, value inside the quote) before the calculator was allowed to use them:

    $ python -m ledgerlens.agent "By what percent did Meta's total revenue grow from fiscal 2023 to fiscal 2024?"
    Route: calculate

    Result: 21.94%

    Formula: (meta_total_revenue_2024 - meta_total_revenue_2023) / meta_total_revenue_2023 * 100

    Numbers used:
    - meta_total_revenue_2024 = 164,501 (META FY2024) [1]
    - meta_total_revenue_2023 = 134,902 (META FY2024) [1]

    Values are as printed in the filings; check the filing for the unit.

    Sources:
    [1] META FY2024 | Item 8. Financial Statements and Supplementary Data

The Meta question is from the dev set, so it shows how the output looks, not how well the system generalises. See Results for sealed test numbers.

## Quick start

Needs Python 3.12, Docker, an OpenAI API key and a contact string for SEC EDGAR. The first run downloads the embedding model (BAAI/bge-small-en-v1.5).

1. Install:

        python3.12 -m venv .venv && source .venv/bin/activate
        pip install -r requirements-dev.txt

2. Create a `.env` file in the project root (it is gitignored):

        OPENAI_API_KEY=your-key
        SEC_USER_AGENT=Your Name your@email.com

3. Start Qdrant (first time):

        docker run -d --name qdrant -p 6333:6333 -v "$(pwd)/data/qdrant_storage:/qdrant/storage" qdrant/qdrant

   Next time: `docker start qdrant`.

4. Build the data (download filings, split into chunks, embed into the `filings` collection):

        python -m ledgerlens.edgar
        python -m ledgerlens.chunker
        python -m ledgerlens.index

5. Ask a question from the command line, or run the API:

        python -m ledgerlens.agent "What were Apple's total net sales in fiscal 2024?"
        uvicorn ledgerlens.api:app --port 8000

   The API has `GET /health` and `POST /ask` with a JSON body `{"question": "..."}`.

6. Run the unit tests: `pytest`

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

## Design decisions

- **Verification is code, not a prompt.** The extractor LLM must return, for every number, the exact quote and the chunk it came from. Plain Python then checks that the quote is inside the chunk, that the value is inside the quote, and that negative values are written in brackets. One failed check rejects the whole list. Asking the model to "be careful" gave no guarantee, so the guarantee had to live outside the model.
- **The formula writer never sees filing text.** It receives only fact names, values, ticker and fiscal year, and writes an expression over those names. Text from a retrieved chunk cannot reach it.
- **The calculator is an AST evaluator** that allows only `+ - * /` and numbers. The model never executes code.
- **Fail safe instead of guessing.** If nothing can be verified, the answer says so. On the first calculation test set this produced one safe failure (t05) instead of a wrong number.
- **Router falls back to lookup** when the LLM output is not valid, so a bad routing response degrades to a cited answer instead of an error.
- **Retrieval: filter first, then claim only what the test shows.** The automatic ticker/year filter was the clear gain on test (hit@1 3/10 to 5/10). Hybrid search is implemented, but its gain over dense + filter is within noise (one question is 10 points), so it is reported that way. A cross-encoder reranker was tried and dropped: no clear gain, 0.5-0.9 s slower per query.
- **Sealed test splits, written before the run and run once.** Dev numbers are labelled tuned. A bug found on dev (a bracketed loss losing its sign) was fixed there, so the dev score is not evidence of generality; the test scores are.

## Project layout

    ledgerlens/        the package
      api.py             FastAPI app: GET /health, POST /ask
      agent.py           agent graph, entry point run(question)
      router.py          decides lookup or calculate
      planner.py         which metrics and years a calculation needs
      query_parser.py    ticker and fiscal-year filter from the question
      search.py          hybrid retrieval (dense + BM25)
      extractor.py, extract_facts.py, facts.py, sanity.py,
      formula_writer.py, calculator.py, calculate.py
                         the calculation path: extract, verify, formula, compute
      edgar.py, processor.py, chunker.py, index.py
                         data pipeline: filings -> sections -> chunks -> Qdrant
      injection.py, injection_harness.py, redteam.py
                         Stage 9 security harness
    eval/              eval scripts, golden sets and every recorded result file
    tests/             unit tests (pytest)
    data/              raw filings, processed chunks, Qdrant storage (not in git)
    Dockerfile, requirements.txt, requirements-dev.txt, pytest.ini

Run the unit tests with `pytest`.

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
