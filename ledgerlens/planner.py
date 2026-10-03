import json

from ledgerlens.ask import LLM_MODEL, get_llm

MAX_METRICS = 4
MAX_LEN = 60

PLANNER_SYSTEM = (
    "You help look up numbers in the SEC 10-K filings of AAPL, AMZN, GOOGL, META and MSFT. "
    'Reply with ONLY a JSON object: {"metrics": ["..."]}. '
    "List the financial line items (at most 4) whose values are needed to answer the question, "
    "each as a short phrase exactly as it would be printed in the financial statements. "
    "Examples: Total net sales, Total revenues, Net income, Operating income, "
    "Research and development, Total assets. "
    "Do not include company names, years, or words like growth, change or percent. "
    "Do not compute anything."
)


class PlanError(ValueError):
    pass


def parse_metrics(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        raise PlanError("planner did not return JSON") from None
    metrics = data.get("metrics") if isinstance(data, dict) else None
    if not isinstance(metrics, list) or not metrics:
        raise PlanError("planner returned no metrics")
    cleaned, seen = [], set()
    for m in metrics:
        if not isinstance(m, str) or not m.strip():
            raise PlanError("metric must be a non-empty string")
        m = " ".join(m.split())
        if len(m) > MAX_LEN:
            raise PlanError("metric too long")
        if m.lower() not in seen:
            seen.add(m.lower())
            cleaned.append(m)
    if len(cleaned) > MAX_METRICS:
        raise PlanError("too many metrics")
    return cleaned


def plan_metrics(question):
    try:
        response = get_llm().chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user", "content": question},
            ],
        )
        content = response.choices[0].message.content
    except Exception as exc:
        raise PlanError(f"LLM call failed: {exc}") from exc
    return parse_metrics(content)
