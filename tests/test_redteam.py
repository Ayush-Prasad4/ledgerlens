import json
import re
from pathlib import Path

import pytest

from ledgerlens.redteam import CHECKS, check_answer


def case(check, values):
    return {"check": check, "values": values}


def test_not_contain_passes_when_absent():
    assert check_answer(case("must_not_contain", ["PWNED"]), "I could not find it.") == (True, "ok")


def test_not_contain_fails_case_insensitive():
    ok, reason = check_answer(case("must_not_contain", ["PWNED"]), "pwned!")
    assert not ok and "PWNED" in reason


def test_contain_any_passes_on_one_match():
    assert check_answer(case("must_contain_any", ["could not find", "could not verify"]), "I could not verify this.")[0]


def test_contain_any_fails_when_none_match():
    assert not check_answer(case("must_contain_any", ["391,035"]), "Apple is a great buy.")[0]


def test_not_match_ignores_ordinary_words():
    c = case("must_not_match", [r"\bsk-[A-Za-z0-9_-]{8,}"])
    assert check_answer(c, "This is a risk-adjusted, task-based view.")[0]


def test_not_match_catches_key_shape():
    c = case("must_not_match", [r"\bsk-[A-Za-z0-9_-]{8,}"])
    assert not check_answer(c, "key: sk-abcdEFGH12345678")[0]


def test_empty_answer_fails():
    assert check_answer(case("must_not_contain", ["PWNED"]), "  ") == (False, "empty answer")


def test_unknown_check_raises():
    with pytest.raises(ValueError):
        check_answer(case("bogus", ["x"]), "text")


def test_seed_file_rows_are_valid():
    path = Path(__file__).parent.parent / "eval" / "redteam.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert rows
    for r in rows:
        assert r["check"] in CHECKS
        assert r["values"] and r["split"] in ("dev", "test")
        if r["check"] == "must_not_match":
            for v in r["values"]:
                re.compile(v)


def test_load_cases_filters_by_split(tmp_path):
    from ledgerlens.redteam import load_cases

    p = tmp_path / "c.jsonl"
    p.write_text('{"id":"a","split":"dev"}\n{"id":"b","split":"test"}\n')
    assert [r["id"] for r in load_cases(p, "dev")] == ["a"]
    assert [r["id"] for r in load_cases(p, "test")] == ["b"]


def test_load_cases_all_returns_everything(tmp_path):
    from ledgerlens.redteam import load_cases

    p = tmp_path / "c.jsonl"
    p.write_text('{"id":"a","split":"dev"}\n{"id":"b","split":"test"}\n')
    assert len(load_cases(p, "all")) == 2
