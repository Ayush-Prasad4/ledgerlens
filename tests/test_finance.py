import pytest

from ledgerlens.finance import growth_percent


def test_growth_up():
    assert growth_percent(100, 110) == pytest.approx(10.0)


def test_growth_down():
    assert growth_percent(200, 150) == pytest.approx(-25.0)


def test_zero_old_value_raises():
    with pytest.raises(ValueError):
        growth_percent(0, 50)
