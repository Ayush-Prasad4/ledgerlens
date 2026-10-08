import pytest

from ledgerlens.injection import insert_poison


def test_middle_puts_poison_in_the_middle():
    points = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]
    out = insert_poison(points, {"id": "P"}, "middle")
    assert [p["id"] for p in out] == [1, 2, "P", 3, 4, 5]


def test_middle_with_no_points():
    assert insert_poison([], {"id": "P"}, "middle") == [{"id": "P"}]


def test_bad_position_still_rejected():
    with pytest.raises(ValueError):
        insert_poison([], {"id": "P"}, "sideways")
