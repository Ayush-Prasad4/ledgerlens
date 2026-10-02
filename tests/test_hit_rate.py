import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))

import hit_rate  # noqa: E402


def entry(**kw):
    base = {"ticker": "AAPL", "fiscal_year": 2023, "must_contain": "383,285"}
    base.update(kw)
    return base


def payload(**kw):
    base = {"ticker": "AAPL", "fiscal_year": 2023, "text": "Total net sales | $383,285 | $394,328"}
    base.update(kw)
    return base


def test_hit_needs_ticker_year_and_keyword():
    assert hit_rate.is_hit(entry(), payload())
    assert not hit_rate.is_hit(entry(), payload(ticker="MSFT"))
    assert not hit_rate.is_hit(entry(), payload(fiscal_year=2024))
    assert not hit_rate.is_hit(entry(), payload(text="no numbers here"))


def test_keyword_list_any_match_passes():
    e = entry(must_contain=["383.3 billion", "383,285"])
    assert hit_rate.is_hit(e, payload())
    assert not hit_rate.is_hit(e, payload(text="something else"))


def test_match_ignores_case_and_accepts_string_year():
    e = entry(must_contain="Apple Intelligence")
    assert hit_rate.is_hit(e, payload(fiscal_year="2023", text="about APPLE INTELLIGENCE features"))


def test_golden_file_is_well_formed():
    entries = hit_rate.load_golden()
    assert len(entries) >= 1
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids))
    for e in entries:
        for field in ("id", "question", "ticker", "fiscal_year", "section", "must_contain"):
            assert field in e, f"{e.get('id')} missing {field}"
        assert isinstance(e["fiscal_year"], int)
        kw = e["must_contain"]
        assert (isinstance(kw, str) and kw) or (isinstance(kw, list) and kw and all(kw))
