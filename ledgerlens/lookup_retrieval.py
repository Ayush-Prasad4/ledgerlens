import logging

from openai import OpenAIError

from ledgerlens.ask import retrieve as base_retrieve
from ledgerlens.calc_retrieval import retrieve_for_metrics
from ledgerlens.planner import plan_metrics
from ledgerlens.query_parser import parse_query, parse_years

log = logging.getLogger(__name__)
EXTRA = 3


def merge_extras(base, extra, limit=EXTRA):
    """Keep base order, then add up to `limit` chunks from `extra` that are not already in base."""
    seen = {p["chunk_id"] for p in base}
    added = []
    for p in extra:
        if p["chunk_id"] in seen:
            continue
        added.append(p)
        seen.add(p["chunk_id"])
        if len(added) == limit:
            break
    return list(base) + added


def retrieve_lookup(question):
    base = base_retrieve(question)
    ticker, year = parse_query(question)
    years = parse_years(question) or ([year] if year else [])
    if not ticker or not years:
        return base
    try:
        metrics = plan_metrics(question)
        extra = retrieve_for_metrics(metrics, ticker, years)
    except (ValueError, OpenAIError) as exc:
        log.warning("planner retrieval skipped: %s", exc)
        return base
    return merge_extras(base, extra)
