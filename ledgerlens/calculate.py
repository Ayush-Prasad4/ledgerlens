from ledgerlens.calc_retrieval import retrieve_for_metrics
from ledgerlens.extract_facts import extract_facts
from ledgerlens.formula import evaluate_formula, used_facts
from ledgerlens.formula_writer import write_formula
from ledgerlens.planner import plan_metrics
from ledgerlens.query_parser import parse_query, parse_years

FAILURE_PREFIX = "I could not verify this calculation from the filings: "


def _failure(reason):
    return {
        "answer": FAILURE_PREFIX + reason,
        "sources": [],
        "calculation": {"ok": False, "error": reason},
    }


def _build_sources(facts, points):
    by_id = {p["chunk_id"]: p for p in points}
    order = []
    for fact in facts:
        if fact["chunk_id"] not in order:
            order.append(fact["chunk_id"])
    sources = []
    for number, chunk_id in enumerate(order, start=1):
        payload = by_id[chunk_id]
        sources.append(
            {
                "id": number,
                "chunk_id": chunk_id,
                "ticker": payload.get("ticker"),
                "fiscal_year": payload.get("fiscal_year"),
                "section": payload.get("section"),
            }
        )
    return sources, {s["chunk_id"]: s["id"] for s in sources}


def _result_label(result, expression):
    # heuristic: a formula that ends with "* 100" is a percent
    text = f"{result:,.2f}"
    if expression.replace(" ", "").endswith("*100"):
        text += "%"
    return text


def _build_answer(result, expression, facts, source_ids):
    lines = [f"Result: {_result_label(result, expression)}", "", f"Formula: {expression}", "", "Numbers used:"]
    for f in facts:
        lines.append(
            f"- {f['name']} = {f['value']:,.10g} ({f['ticker']} FY{f['fiscal_year']}) "
            f"[{source_ids[f['chunk_id']]}]"
        )
    lines += ["", "Values are as printed in the filings; check the filing for the unit."]
    return "\n".join(lines)


def calculate_answer(question):
    ticker, _ = parse_query(question)
    years = parse_years(question)
    if not ticker:
        return _failure("could not tell which single company the question is about")
    if not years:
        return _failure("no fiscal year found in the question")
    try:
        metrics = plan_metrics(question)
        points = retrieve_for_metrics(metrics, ticker, years)
        facts = extract_facts(question, points)
        expression = write_formula(question, facts)
        numeric, result = evaluate_formula(expression, facts)
        facts = used_facts(expression, facts)
    except ValueError as exc:
        return _failure(str(exc))
    sources, source_ids = _build_sources(facts, points)
    return {
        "answer": _build_answer(result, expression, facts, source_ids),
        "sources": sources,
        "calculation": {
            "ok": True,
            "facts": facts,
            "formula": expression,
            "numeric_expression": numeric,
            "result": result,
        },
    }
