from decimal import Decimal

import pytest

from solution import shipping_cost as sc


def test_basic_weights():
    assert sc(10, 10, 10, 0.5, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1.1, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 2, 1, 0) == Decimal("11.00")
    assert str(sc(10, 10, 10, 2, 1, 0)) == "11.00"


def test_volumetric():
    # 50*50*20/5000 = 10 kg -> 8 + 1.5*18 = 35
    assert sc(50, 50, 20, 1, 1, 0) == Decimal("35.00")


def test_zones():
    assert sc(10, 10, 10, 1, 2, 0) == Decimal("10.00")
    assert sc(10, 10, 10, 1, 3, 0) == Decimal("12.80")


def test_free_shipping():
    assert sc(10, 10, 10, 1, 1, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 2, Decimal("150")) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 3, 150) == Decimal("12.80")
    assert sc(10, 10, 10, 1, 1, 149.99) == Decimal("8.00")


def test_oversize():
    assert sc(120, 1, 1, 1, 1, 0) == Decimal("8.00")
    assert sc(121, 1, 1, 1, 3, 0) == Decimal("24.80")
    assert sc(121, 1, 1, 1, 1, 200) == Decimal("12.00")


def test_rounding_half_up():
    # 8.00*1.25 + 1.5*1.25 = 11.875 -> 11.88
    assert sc(10, 10, 10, 1.5, 2, 0) == Decimal("11.88")


def test_float_str_conversion():
    assert sc(10, 10, 10, 0.1, 1, 0.1) == Decimal("8.00")


@pytest.mark.parametrize("bad", [True, "1", None, [1]])
def test_type_errors(bad):
    with pytest.raises(TypeError):
        sc(bad, 1, 1, 1, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, 1, 1, bad)


@pytest.mark.parametrize(
    "args",
    [
        (0, 1, 1, 1, 1, 0),
        (1, -1, 1, 1, 1, 0),
        (1, 1, 0, 1, 1, 0),
        (1, 1, 1, 0, 1, 0),
        (1, 1, 1, 1, 1, -1),
        (1, 1, 1, float("nan"), 1, 0),
        (1, 1, 1, float("inf"), 1, 0),
        (1, 1, 1, 1, 0, 0),
        (1, 1, 1, 1, 4, 0),
        (1, 1, 1, 1, True, 0),
        (1, 1, 1, 1, 1.0, 0),
        (1, 1, 1, 1, "1", 0),
    ],
)
def test_value_errors(args):
    with pytest.raises(ValueError):
        sc(*args)
