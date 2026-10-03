import json
import logging

from ledgerlens.ask import LLM_MODEL, get_llm

log = logging.getLogger(__name__)

ROUTES = ("lookup", "calculate")

ROUTER_SYSTEM = (
    "You route questions about the SEC 10-K filings of AAPL, AMZN, GOOGL, META and MSFT. "
    'Reply with ONLY a JSON object, either {"route": "lookup"} or {"route": "calculate"}. '
    '"lookup" means the answer is a fact stated in the filings (a number, a list, a description). '
    '"calculate" means the answer needs arithmetic on several numbers: growth, change, '
    "percentage, ratio, margin, difference, sum, or a comparison between years or companies."
)


def parse_route(text):
    try:
        route = json.loads(text).get("route")
    except (ValueError, AttributeError, TypeError):
        return "lookup"
    return route if route in ROUTES else "lookup"


def route_question(question):
    try:
        response = get_llm().chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM},
                {"role": "user", "content": question},
            ],
        )
        return parse_route(response.choices[0].message.content)
    except Exception as exc:
        log.warning("router failed, falling back to lookup: %s", exc)
        return "lookup"
