from decimal import Decimal

import pytest

from solution import shipping_cost as sc


def test_basic_weights():
    assert sc(10, 10, 10, 0.5, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1.1, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 1.5, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 2, 1, 0) == Decimal("11.00")
    assert sc(10, 10, 10, 2.01, 1, 0) == Decimal("12.50")


def test_result_type_and_places():
    r = sc(10, 10, 10, 1, 1, 0)
    assert isinstance(r, Decimal)
    assert str(r) == "8.00"


def test_volumetric():
    # 50*40*30/5000 = 12 kg -> 8 + 1.5*22
    assert sc(50, 40, 30, 1, 1, 0) == Decimal("41.00")
    # weight larger than volumetric
    assert sc(10, 10, 10, 3, 1, 0) == Decimal("14.00")


def test_zones():
    assert sc(10, 10, 10, 2, 2, 0) == Decimal("13.75")
    assert sc(10, 10, 10, 2, 3, 0) == Decimal("17.60")
    assert sc(10, 10, 10, 1, 3, 0) == Decimal("12.80")


def test_free_shipping():
    assert sc(10, 10, 10, 2, 1, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 2, 2, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 2, 1, Decimal("149.99")) == Decimal("11.00")
    assert sc(10, 10, 10, 2, 3, 500) == Decimal("17.60")


def test_oversize():
    assert sc(120, 1, 1, 1, 1, 0) == Decimal("8.00")
    assert sc(121, 1, 1, 1, 1, 0) == Decimal("20.00")
    assert sc(1, 130, 1, 1, 1, 0) == Decimal("20.00")
    assert sc(1, 1, 130, 1, 1, 0) == Decimal("20.00")
    assert sc(121, 1, 1, 1, 1, 200) == Decimal("12.00")
    assert sc(121, 1, 1, 1, 3, 0) == Decimal("24.80")


def test_rounding_half_up():
    # 8 + 1.5 = 9.5 * 1.25 = 11.875 -> 11.88
    assert sc(10, 10, 10, 1.5, 2, 0) == Decimal("11.88")


def test_float_via_str():
    assert sc(10, 10, 10, 0.1, 1, 0) == Decimal("8.00")
    assert sc(Decimal("10"), 10, 10, 1, 1, 0) == Decimal("8.00")


@pytest.mark.parametrize("bad", ["1", None, True, [1]])
def test_type_errors(bad):
    with pytest.raises(TypeError):
        sc(bad, 1, 1, 1, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, bad, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, 1, 1, bad)


@pytest.mark.parametrize(
    "args",
    [
        (0, 1, 1, 1, 1, 0),
        (1, 0, 1, 1, 1, 0),
        (1, 1, 0, 1, 1, 0),
        (1, 1, 1, 0, 1, 0),
        (-1, 1, 1, 1, 1, 0),
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


def test_zero_subtotal_ok():
    assert sc(1, 1, 1, 1, 1, 0) == Decimal("8.00")
