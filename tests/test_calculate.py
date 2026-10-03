import pytest

from ledgerlens import calculate
from ledgerlens.calculator import CalculatorError
from ledgerlens.facts import FactError
from ledgerlens.formula_writer import FormulaError
from ledgerlens.planner import PlanError

GROWTH = "(aapl_net_sales_2024 - aapl_net_sales_2023) / aapl_net_sales_2023 * 100"
POINTS = [
    {"chunk_id": "AAPL-2024-0093", "ticker": "AAPL", "fiscal_year": 2024, "section": "Item 8"},
    {"chunk_id": "AAPL-2023-0091", "ticker": "AAPL", "fiscal_year": 2023, "section": "Item 8"},
]


def make_facts(same_chunk=False):
    second_chunk = "AAPL-2024-0093" if same_chunk else "AAPL-2023-0091"
    return [
        {"name": "aapl_net_sales_2024", "value": 391035.0, "chunk_id": "AAPL-2024-0093",
         "ticker": "AAPL", "fiscal_year": 2024, "quote": "q"},
        {"name": "aapl_net_sales_2023", "value": 383285.0, "chunk_id": second_chunk,
         "ticker": "AAPL", "fiscal_year": 2023, "quote": "q"},
    ]


def patch_pipeline(monkeypatch, ticker="AAPL", years=(2023, 2024), plan=None,
                   extract=None, formula=None, facts=None):
    calls = []

    def fake_plan(question):
        calls.append("plan")
        if plan:
            raise plan
        return ["Net sales"]

    def fake_extract(question, points):
        if extract:
            raise extract
        return facts if facts is not None else make_facts()

    def fake_formula(question, facts_):
        if formula:
            raise formula
        return GROWTH

    monkeypatch.setattr(calculate, "parse_query", lambda q: (ticker, 2024))
    monkeypatch.setattr(calculate, "parse_years", lambda q: list(years))
    monkeypatch.setattr(calculate, "plan_metrics", fake_plan)
    monkeypatch.setattr(calculate, "retrieve_for_metrics", lambda m, t, y: POINTS)
    monkeypatch.setattr(calculate, "extract_facts", fake_extract)
    monkeypatch.setattr(calculate, "write_formula", fake_formula)
    return calls


def test_success(monkeypatch):
    patch_pipeline(monkeypatch)
    out = calculate.calculate_answer("Apple sales growth fiscal 2023 to fiscal 2024?")
    assert out["calculation"]["ok"] is True
    assert out["calculation"]["result"] == pytest.approx(2.0220, abs=1e-3)
    assert "Result: 2.02" in out["answer"]
    assert GROWTH in out["answer"]
    assert "aapl_net_sales_2024 = 391,035 (AAPL FY2024) [1]" in out["answer"]
    assert "aapl_net_sales_2023 = 383,285 (AAPL FY2023) [2]" in out["answer"]
    assert [s["chunk_id"] for s in out["sources"]] == ["AAPL-2024-0093", "AAPL-2023-0091"]


def test_same_chunk_gives_one_source(monkeypatch):
    patch_pipeline(monkeypatch, facts=make_facts(same_chunk=True))
    out = calculate.calculate_answer("q")
    assert len(out["sources"]) == 1
    assert out["answer"].count("[1]") == 2


def test_no_company_stops_before_llm(monkeypatch):
    calls = patch_pipeline(monkeypatch, ticker=None)
    out = calculate.calculate_answer("q")
    assert out["answer"].startswith(calculate.FAILURE_PREFIX)
    assert out["calculation"]["ok"] is False
    assert calls == []


def test_no_year_stops_before_llm(monkeypatch):
    calls = patch_pipeline(monkeypatch, years=())
    out = calculate.calculate_answer("q")
    assert "no fiscal year" in out["answer"]
    assert calls == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"plan": PlanError("planner broke")},
        {"extract": FactError("fact not verified")},
        {"formula": FormulaError("bad formula")},
    ],
)
def test_pipeline_errors_become_clear_failure(monkeypatch, kwargs):
    patch_pipeline(monkeypatch, **kwargs)
    out = calculate.calculate_answer("q")
    assert out["answer"].startswith(calculate.FAILURE_PREFIX)
    assert out["sources"] == []
    assert out["calculation"]["ok"] is False


def test_unknown_name_in_formula_is_failure(monkeypatch):
    patch_pipeline(monkeypatch)
    monkeypatch.setattr(calculate, "write_formula", lambda q, f: "x / y")
    out = calculate.calculate_answer("q")
    assert out["answer"].startswith(calculate.FAILURE_PREFIX)
    assert "unknown names" in out["answer"]
