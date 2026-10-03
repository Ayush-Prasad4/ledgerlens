import json

from ledgerlens.ask import LLM_MODEL, get_llm
from ledgerlens.extractor import verify_facts
from ledgerlens.facts import FactError

EXTRACT_SYSTEM = (
    "You extract numbers from excerpts of SEC 10-K filings so they can be used in a calculation. "
    'Reply with ONLY a JSON object: {"facts": [{"name": ..., "value": ..., "quote": ..., "chunk_id": ...}]}. '
    "name: lowercase letters, digits and underscores only, starting with a letter, "
    "include company and year (example: aapl_net_sales_2024). "
    "value: the number exactly as printed in the excerpt, digits and commas only, no currency sign, no unit. "
    "quote: copy-paste the short piece of the excerpt that contains the number, character for character. "
    "chunk_id: the chunk_id of the excerpt you copied it from. "
    "Extract only the numbers needed to answer the question, one fact per number, "
    "and only from the excerpts given. Never compute, round or guess. "
    'If a needed number is not in the excerpts, return {"facts": []}.'
)


def build_extract_context(points):
    parts = []
    for p in points:
        header = f"[chunk_id={p['chunk_id']} | {p.get('ticker')} FY{p.get('fiscal_year')} | {p.get('section')}]"
        parts.append(f"{header}\n{p['text']}")
    return "\n\n".join(parts)


def parse_facts_json(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        raise FactError("extractor did not return JSON") from None
    facts = data.get("facts") if isinstance(data, dict) else None
    if not isinstance(facts, list):
        raise FactError("extractor reply has no facts list")
    return facts


def extract_facts(question, points):
    """Ask the LLM for numbers, then verify every one against the chunks.

    Raises FactError on any problem (API error, bad JSON, unverifiable fact).
    """
    user = f"Question: {question}\n\nExcerpts:\n{build_extract_context(points)}"
    try:
        response = get_llm().chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
    except Exception as exc:
        raise FactError(f"LLM call failed: {exc}") from exc
    return verify_facts(parse_facts_json(content), points)
