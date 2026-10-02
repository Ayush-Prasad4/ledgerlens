from ledgerlens.search import build_filter, rrf_fuse, tokenize


def test_tokenize_keeps_decimal_and_comma_numbers():
    assert "307.4" in tokenize("Revenues were $307.4 billion")
    assert "383,285" in tokenize("net sales of 383,285 million")


def test_rrf_puts_item_ranked_first_in_both_lists_on_top():
    fused = rrf_fuse([["a", "b"], ["a", "c"]], [1.0, 1.0])
    assert fused[0][1] == "a"
    assert {cid for _, cid in fused} == {"a", "b", "c"}


def test_rrf_weight_can_flip_the_order():
    # a is first in list 1, b is first in list 2; list 2 has 3x weight
    fused = rrf_fuse([["a", "b"], ["b", "a"]], [1.0, 3.0])
    assert fused[0][1] == "b"


def test_build_filter_none_when_no_conditions():
    assert build_filter() is None


def test_build_filter_uses_int_fiscal_year():
    f = build_filter("GOOGL", "2023")
    assert [c.key for c in f.must] == ["ticker", "fiscal_year"]
    assert f.must[0].match.value == "GOOGL"
    assert f.must[1].match.value == 2023
    assert isinstance(f.must[1].match.value, int)
