from ledgerlens.calculate import _result_label


def test_percent_formula_gets_percent_sign():
    assert _result_label(2.0219, "(a - b) / b * 100") == "2.02%"


def test_non_percent_formula_has_no_sign():
    assert _result_label(33147.0, "a - b") == "33,147.00"


def test_percent_detected_without_spaces():
    assert _result_label(12.0389, "a/b*100") == "12.04%"


def test_times_1000_is_not_percent():
    assert _result_label(5.0, "a / b * 1000") == "5.00"
