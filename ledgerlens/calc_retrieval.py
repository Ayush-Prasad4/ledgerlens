import re

from ledgerlens.ask import RETRIEVAL_MODE
from ledgerlens.search import search


def _revenue_twin(phrase):
    """'Total revenues' <-> 'Total revenue': Microsoft and Meta print the singular, Alphabet the plural."""
    if re.search(r"revenues", phrase, re.IGNORECASE):
        return re.sub(r"(revenue)s", r"\1", phrase, flags=re.IGNORECASE)
    if re.search(r"revenue", phrase, re.IGNORECASE):
        return re.sub(r"(revenue)", r"\1s", phrase, flags=re.IGNORECASE)
    return None


def query_variants(metric):
    """Planner phrase, a 'Total ...' form for sales/revenue lines, and the singular/plural
    twin of 'revenue(s)' (companies print 'Total revenue' or 'Total revenues')."""
    variants = [metric]
    low = metric.lower()
    if ("sales" in low or "revenue" in low) and not low.startswith("total"):
        variants.append("Total " + metric[0].lower() + metric[1:])
    for v in list(variants):
        twin = _revenue_twin(v)
        if twin and twin not in variants:
            variants.append(twin)
    return variants


def retrieve_for_metrics(metrics, ticker, years, per_query=5, max_points=24):
    """One search per (year, metric, variant); merge rank by rank, dedupe, cap."""
    if not ticker or not years:
        raise ValueError("need one company and at least one fiscal year")
    lists = []
    for year in years:
        for metric in metrics:
            for query in query_variants(metric):
                hits = search(
                    query, limit=per_query, ticker=ticker, fiscal_year=year, mode=RETRIEVAL_MODE
                )
                lists.append([payload for _score, payload in hits])
    points, seen = [], set()
    for rank in range(per_query):
        for result in lists:
            if rank < len(result) and result[rank]["chunk_id"] not in seen:
                seen.add(result[rank]["chunk_id"])
                points.append(result[rank])
                if len(points) >= max_points:
                    return points
    return points
