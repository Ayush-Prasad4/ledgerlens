import json
from types import SimpleNamespace

import pytest

from ledgerlens.extract_facts import build_extract_context, extract_facts, parse_facts_json
from ledgerlens.facts import FactError

POINTS = [
    {
        "chunk_id": "c1",
        "ticker": "AAPL",
        "fiscal_year": 2024,
        "section": "Item 7",
        "text": "Net sales were $391,035 million in 2024 and $383,285 million in 2023.",
    }
]
GOOD = {
    "name": "aapl_net_sales_2024",
    "value": "391,035",
    "quote": "Net sales were $391,035 million in 2024",
    "chunk_id": "c1",
}


def fake_llm(content=None, error=None):
    def create(**kwargs):
        if error:
            raise error
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    completions = SimpleNamespace(create=create)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def patch_llm(monkeypatch, **kwargs):
    monkeypatch.setattr("ledgerlens.extract_facts.get_llm", lambda: fake_llm(**kwargs))


def test_build_context_has_chunk_id_and_text():
    context = build_extract_context(POINTS)
    assert "chunk_id=c1" in context
    assert "AAPL FY2024" in context
    assert "$391,035 million" in context


def test_parse_facts_json_ok():
    assert parse_facts_json(json.dumps({"facts": [GOOD]})) == [GOOD]


@pytest.mark.parametrize("text", ["not json", "[]", '{"facts": 5}', None])
def test_parse_facts_json_bad(text):
    with pytest.raises(FactError):
        parse_facts_json(text)


def test_extract_facts_ok(monkeypatch):
    patch_llm(monkeypatch, content=json.dumps({"facts": [GOOD]}))
    result = extract_facts("AAPL sales 2024?", POINTS)
    assert result[0]["value"] == 391035.0
    assert result[0]["fiscal_year"] == 2024


def test_extract_facts_non_json(monkeypatch):
    patch_llm(monkeypatch, content="sorry, here you go")
    with pytest.raises(FactError):
        extract_facts("q", POINTS)


def test_extract_facts_hallucinated_quote(monkeypatch):
    bad = dict(GOOD, quote="Revenue reached $391,035 million")
    patch_llm(monkeypatch, content=json.dumps({"facts": [bad]}))
    with pytest.raises(FactError):
        extract_facts("q", POINTS)


def test_extract_facts_api_error(monkeypatch):
    patch_llm(monkeypatch, error=RuntimeError("boom"))
    with pytest.raises(FactError):
        extract_facts("q", POINTS)


def test_extract_facts_empty_list(monkeypatch):
    patch_llm(monkeypatch, content=json.dumps({"facts": []}))
    with pytest.raises(FactError):
        extract_facts("q", POINTS)
