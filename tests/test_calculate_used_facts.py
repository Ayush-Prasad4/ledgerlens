from ledgerlens import calculate


def test_calculate_answer_drops_fact_not_in_formula(monkeypatch):
    facts = [
        {"name": "meta_total_revenue_2024", "value": 150, "ticker": "META", "fiscal_year": 2024, "chunk_id": "c1"},
        {"name": "zx_canary_8830", "value": 1, "ticker": "META", "fiscal_year": 2024, "chunk_id": "c9"},
        {"name": "meta_total_revenue_2023", "value": 100, "ticker": "META", "fiscal_year": 2024, "chunk_id": "c1"},
    ]
    expression = "(meta_total_revenue_2024 - meta_total_revenue_2023) / meta_total_revenue_2023 * 100"
    monkeypatch.setattr(calculate, "parse_query", lambda q: ("META", None))
    monkeypatch.setattr(calculate, "parse_years", lambda q: [2023, 2024])
    monkeypatch.setattr(calculate, "plan_metrics", lambda q: ["Total revenue"])
    monkeypatch.setattr(calculate, "retrieve_for_metrics", lambda m, t, y: [])
    monkeypatch.setattr(calculate, "extract_facts", lambda q, p: facts)
    monkeypatch.setattr(calculate, "write_formula", lambda q, f: expression)
    monkeypatch.setattr(calculate, "_build_sources", lambda f, p: ([], []))
    monkeypatch.setattr(calculate, "_build_answer", lambda r, e, f, s: "ok")

    out = calculate.calculate_answer("By what percent did Meta's total revenue grow from fiscal 2023 to fiscal 2024?")

    assert out["calculation"]["ok"] is True
    assert out["calculation"]["result"] == 50.0
    assert [f["name"] for f in out["calculation"]["facts"]] == ["meta_total_revenue_2024", "meta_total_revenue_2023"]
