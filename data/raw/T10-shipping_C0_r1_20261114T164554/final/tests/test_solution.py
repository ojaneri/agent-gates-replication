from decimal import Decimal

import pytest

from solution import shipping_cost as sc


def test_basic_weights():
    assert sc(10, 10, 10, 0.5, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1.2, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 2, 1, 0) == Decimal("11.00")
    assert sc(10, 10, 10, 2.01, 1, 0) == Decimal("12.50")


def test_volumetric():
    # 50*40*30/5000 = 12
    assert sc(50, 40, 30, 1, 1, 0) == Decimal("8") + Decimal("1.5") * 22


def test_zones():
    assert sc(10, 10, 10, 1, 2, 0) == Decimal("10.00")
    assert sc(10, 10, 10, 1, 3, 0) == Decimal("12.80")
    assert sc(10, 10, 10, 1.5, 3, 0) == Decimal("15.20")


def test_free_shipping():
    assert sc(10, 10, 10, 1, 1, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 2, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 3, 150) == Decimal("12.80")
    assert sc(10, 10, 10, 1, 1, Decimal("149.99")) == Decimal("8.00")


def test_oversize():
    assert sc(120, 1, 1, 1, 1, 0) == Decimal("8.00")
    assert sc(121, 1, 1, 1, 1, 0) == Decimal("20.00")
    assert sc(121, 1, 1, 1, 3, 0) == Decimal("24.80")
    assert sc(1, 1, 130, 1, 1, 200) == Decimal("12.00")


def test_returns_two_places():
    r = sc(1, 1, 1, 1, 1, 0)
    assert isinstance(r, Decimal)
    assert r.as_tuple().exponent == -2


def test_float_str_and_decimal():
    assert sc(10, 10, 10, 0.1, 1, 0.0) == Decimal("8.00")
    assert sc(Decimal("10"), 10, 10, Decimal("1.5"), 1, 0) == Decimal("9.50")


def test_type_errors():
    for bad in (True, "1", None, [1]):
        with pytest.raises(TypeError):
            sc(bad, 1, 1, 1, 1, 0)
        with pytest.raises(TypeError):
            sc(1, 1, 1, 1, 1, bad)
        with pytest.raises(TypeError):
            sc(1, 1, 1, bad, 1, 0)


def test_value_errors():
    for args in [(0, 1, 1, 1, 1, 0), (1, -1, 1, 1, 1, 0), (1, 1, 0, 1, 1, 0),
                 (1, 1, 1, 0, 1, 0), (1, 1, 1, 1, 1, -1),
                 (1, 1, 1, 1, 0, 0), (1, 1, 1, 1, 4, 0), (1, 1, 1, 1, True, 0),
                 (1, 1, 1, 1, 1.0, 0), (1, 1, 1, 1, "1", 0)]:
        with pytest.raises(ValueError):
            sc(*args)
