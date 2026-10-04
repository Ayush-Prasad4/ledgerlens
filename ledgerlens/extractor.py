import re

from ledgerlens.facts import FactError, number_in_text, parse_number

_NAME_RE = re.compile(r"[a-z][a-z0-9_]*")


def _norm(text):
    return " ".join(text.split())


def verify_fact(fact, chunks):
    """Check one LLM-claimed fact against the retrieved chunks.

    fact: dict with name, value (string), quote, chunk_id
    chunks: dict chunk_id -> payload dict (needs 'text')
    """
    if not isinstance(fact, dict):
        raise FactError("fact must be an object")
    for key in ("name", "value", "quote", "chunk_id"):
        if not isinstance(fact.get(key), str) or not fact[key].strip():
            raise FactError(f"missing or empty field: {key}")
    if not _NAME_RE.fullmatch(fact["name"]):
        raise FactError(f"bad name: {fact['name']!r}")
    chunk = chunks.get(fact["chunk_id"])
    if chunk is None:
        raise FactError(f"unknown chunk_id: {fact['chunk_id']!r}")
    if _norm(fact["quote"]) not in _norm(chunk["text"]):
        raise FactError(f"quote not found in chunk for {fact['name']}")
    if not number_in_text(fact["value"], fact["quote"]):
        raise FactError(
            f"value not found in quote for {fact['name']} "
            "(negative numbers must keep their brackets)"
        )
    return {
        "name": fact["name"],
        "value": parse_number(fact["value"]),
        "chunk_id": fact["chunk_id"],
        "ticker": chunk.get("ticker"),
        "fiscal_year": chunk.get("fiscal_year"),
        "quote": fact["quote"],
    }


def verify_facts(raw_facts, points):
    """All-or-nothing: one bad fact rejects the whole list."""
    if not isinstance(raw_facts, list) or not raw_facts:
        raise FactError("no facts returned")
    chunks = {p["chunk_id"]: p for p in points}
    verified = []
    seen = set()
    for fact in raw_facts:
        item = verify_fact(fact, chunks)
        if item["name"] in seen:
            raise FactError(f"duplicate name: {item['name']}")
        seen.add(item["name"])
        verified.append(item)
    return verified
