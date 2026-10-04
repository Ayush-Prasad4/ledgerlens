from ledgerlens.calc_retrieval import query_variants


def test_plural_revenues_also_tries_singular():
    assert query_variants("Total revenues") == ["Total revenues", "Total revenue"]


def test_singular_revenue_also_tries_plural():
    assert query_variants("Total revenue") == ["Total revenue", "Total revenues"]


def test_bare_revenue_gets_total_form_and_both_twins():
    assert query_variants("Revenue") == ["Revenue", "Total revenue", "Revenues", "Total revenues"]


def test_twin_keeps_the_original_capitalisation():
    assert query_variants("Total Revenues") == ["Total Revenues", "Total Revenue"]


def test_sales_lines_have_no_revenue_twin():
    assert query_variants("Net sales") == ["Net sales", "Total net sales"]
    assert query_variants("Total net sales") == ["Total net sales"]


def test_other_metrics_are_left_alone():
    assert query_variants("Net income") == ["Net income"]
    assert query_variants("Research and development") == ["Research and development"]
