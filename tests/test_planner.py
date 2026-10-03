import json
from types import SimpleNamespace

import pytest

from ledgerlens.planner import PlanError, parse_metrics, plan_metrics


def patch_llm(monkeypatch, content=None, error=None, seen=None):
    def create(**kwargs):
        if seen is not None:
            seen.append(kwargs)
        if error:
            raise error
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr("ledgerlens.planner.get_llm", lambda: client)


def test_parse_metrics_ok():
    assert parse_metrics('{"metrics": ["Total net sales"]}') == ["Total net sales"]


def test_parse_metrics_dedupes_and_cleans():
    text = json.dumps({"metrics": ["Total net sales", "  total   net sales ", "Net income"]})
    assert parse_metrics(text) == ["Total net sales", "Net income"]


@pytest.mark.parametrize(
    "text",
    ["not json", "[]", '{"metrics": []}', '{"metrics": "x"}', '{"metrics": [1]}', None],
)
def test_parse_metrics_bad(text):
    with pytest.raises(PlanError):
        parse_metrics(text)


def test_parse_metrics_too_many():
    text = json.dumps({"metrics": ["a", "b", "c", "d", "e"]})
    with pytest.raises(PlanError):
        parse_metrics(text)


def test_parse_metrics_too_long():
    text = json.dumps({"metrics": ["x" * 61]})
    with pytest.raises(PlanError):
        parse_metrics(text)


def test_plan_metrics_ok(monkeypatch):
    seen = []
    patch_llm(monkeypatch, content='{"metrics": ["Total net sales"]}', seen=seen)
    assert plan_metrics("Apple sales growth 2023 to 2024?") == ["Total net sales"]
    assert seen[0]["messages"][1]["content"] == "Apple sales growth 2023 to 2024?"


def test_plan_metrics_api_error(monkeypatch):
    patch_llm(monkeypatch, error=RuntimeError("boom"))
    with pytest.raises(PlanError):
        plan_metrics("q")


def test_plan_metrics_bad_output(monkeypatch):
    patch_llm(monkeypatch, content="sure thing")
    with pytest.raises(PlanError):
        plan_metrics("q")
