from ledgerlens.formula import used_facts


def _facts(*names):
    return [{"name": n, "value": 1} for n in names]


def test_unused_fact_is_dropped():
    facts = _facts("meta_total_revenue_2024", "zx_canary_8830", "meta_total_revenue_2023")
    kept = used_facts("(meta_total_revenue_2024 - meta_total_revenue_2023) / meta_total_revenue_2023", facts)
    assert [f["name"] for f in kept] == ["meta_total_revenue_2024", "meta_total_revenue_2023"]


def test_all_used_facts_unchanged():
    facts = _facts("a_2024", "a_2023")
    assert used_facts("a_2024 / a_2023", facts) == facts


def test_expression_without_names_keeps_nothing():
    assert used_facts("1 + 2", _facts("a_2024")) == []
