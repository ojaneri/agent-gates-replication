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
    # 50*40*30/5000 = 12 kg -> 8 + 1.5*22 = 41
    assert sc(50, 40, 30, 1, 1, 0) == Decimal("41.00")
    # actual heavier than volumetric
    assert sc(10, 10, 10, 3, 1, 0) == Decimal("14.00")


def test_zones():
    assert sc(10, 10, 10, 1, 2, 0) == Decimal("10.00")
    assert sc(10, 10, 10, 1, 3, 0) == Decimal("12.80")
    assert sc(10, 10, 10, 1.5, 3, 0) == Decimal("15.20")


def test_free_shipping():
    assert sc(10, 10, 10, 1, 1, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 2, 200) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 1, Decimal("149.99")) == Decimal("8.00")
    assert sc(10, 10, 10, 1, 3, 500) == Decimal("12.80")


def test_oversize():
    assert sc(120, 1, 1, 1, 1, 0) == Decimal("8.00")
    assert sc(10, 121, 10, 1, 1, 0) == Decimal("24.50")
    assert sc(130, 1, 1, 1, 1, 150) == Decimal("12.00")
    assert sc(130, 1, 1, 1, 2, 0) == Decimal("22.00")


def test_float_and_decimal_inputs():
    assert sc(Decimal("10"), 10.0, 10, 0.1, 1, 0.0) == Decimal("8.00")
    assert sc(10, 10, 10, Decimal("1.5"), 1, 0) == Decimal("9.50")


def test_rounding_half_up():
    # 8 + 1.5 = 9.5 * 1.25 = 11.875 -> 11.88
    assert sc(10, 10, 10, 1.5, 2, 0) == Decimal("11.88")


@pytest.mark.parametrize("bad", [True, "1", None, [1]])
def test_type_errors(bad):
    with pytest.raises(TypeError):
        sc(bad, 1, 1, 1, 1, 0)
    with pytest.raises(TypeError):
        sc(1, bad, 1, 1, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, bad, 1, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, bad, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, 1, 1, bad)


@pytest.mark.parametrize(
    "args",
    [
        (0, 1, 1, 1, 1, 0),
        (1, 0, 1, 1, 1, 0),
        (1, 1, -1, 1, 1, 0),
        (1, 1, 1, 0, 1, 0),
        (1, 1, 1, 1, 1, -1),
        (1, 1, 1, float("nan"), 1, 0),
        (1, 1, 1, float("inf"), 1, 0),
    ],
)
def test_value_errors(args):
    with pytest.raises(ValueError):
        sc(*args)


@pytest.mark.parametrize("zone", [0, 4, True, 1.0, "1", None, -1])
def test_bad_zone(zone):
    with pytest.raises(ValueError):
        sc(1, 1, 1, 1, zone, 0)
