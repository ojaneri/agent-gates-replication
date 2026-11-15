from decimal import Decimal
import pytest
from solution import shipping_cost as sc


def test_base_weights():
    assert sc(10, 10, 10, 0.5, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1.1, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 2, 1, 0) == Decimal("11.00")


def test_volumetric():
    # 50*50*20/5000 = 10kg -> 8 + 1.5*18 = 35
    assert sc(50, 50, 20, 1, 1, 0) == Decimal("35.00")


def test_zones():
    assert sc(10, 10, 10, 1, 2, 0) == Decimal("10.00")
    assert sc(10, 10, 10, 1, 3, 0) == Decimal("12.80")


def test_free_shipping():
    assert sc(10, 10, 10, 1, 1, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 2, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 3, 150) == Decimal("12.80")
    assert sc(10, 10, 10, 1, 1, Decimal("149.99")) == Decimal("8.00")


def test_oversize():
    assert sc(120, 1, 1, 1, 1, 0) == Decimal("8.00")
    assert sc(121, 1, 1, 1, 1, 0) == Decimal("20.00")
    assert sc(121, 1, 1, 1, 1, 200) == Decimal("12.00")


def test_rounding_and_type():
    r = sc(10, 10, 10, 1.5, 2, 0)
    assert r == Decimal("11.88") and r.as_tuple().exponent == -2


def test_float_str():
    assert sc(10, 10, 10, 0.1, 1, 0) == Decimal("8.00")


def test_type_errors():
    for bad in (True, "1", None):
        with pytest.raises(TypeError):
            sc(bad, 1, 1, 1, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, 1, 1, "0")


def test_value_errors():
    with pytest.raises(ValueError):
        sc(0, 1, 1, 1, 1, 0)
    with pytest.raises(ValueError):
        sc(1, 1, 1, -1, 1, 0)
    with pytest.raises(ValueError):
        sc(1, 1, 1, 1, 1, -1)
    for z in (0, 4, True, 1.0, "1"):
        with pytest.raises(ValueError):
            sc(1, 1, 1, 1, z, 0)
