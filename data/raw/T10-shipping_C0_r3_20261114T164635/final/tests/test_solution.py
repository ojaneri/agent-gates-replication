from decimal import Decimal

import pytest

from solution import shipping_cost as sc


def test_basic_weights():
    assert sc(10, 10, 10, 0.3, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1.5, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 2, 1, 0) == Decimal("11.00")
    assert sc(10, 10, 10, 1.01, 1, 0) == Decimal("9.50")


def test_returns_decimal_two_places():
    r = sc(10, 10, 10, 1, 1, 0)
    assert isinstance(r, Decimal)
    assert r.as_tuple().exponent == -2


def test_volumetric():
    # 50*50*20/5000 = 10 kg -> 8 + 18*1.5 = 35
    assert sc(50, 50, 20, 1, 1, 0) == Decimal("35.00")


def test_zones():
    assert sc(10, 10, 10, 2, 2, 0) == Decimal("13.75")
    assert sc(10, 10, 10, 2, 3, 0) == Decimal("17.60")


def test_free_shipping():
    assert sc(10, 10, 10, 2, 1, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 2, 2, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 2, 3, 150) == Decimal("17.60")
    assert sc(10, 10, 10, 2, 1, Decimal("149.99")) == Decimal("11.00")


def test_oversize():
    # 120 not oversize; 121 is. vol 121*10*10/5000=2.42 -> 2.5 -> 12.50
    assert sc(120, 10, 10, 1, 1, 0) == Decimal("12.50")
    assert sc(121, 10, 10, 1, 1, 0) == Decimal("24.50")
    assert sc(121, 10, 10, 1, 1, 200) == Decimal("12.00")
    assert sc(121, 10, 10, 1, 3, 0) == Decimal("12.00") + Decimal("12.50") * Decimal("1.6")


def test_rounding_half_up():
    # 8 * 1.25 = 10; 9.5*1.25 = 11.875 -> 11.88
    assert sc(10, 10, 10, 1.5, 2, 0) == Decimal("11.88")


def test_float_via_str():
    assert sc(0.1, 0.1, 0.1, 0.1, 1, 0.1) == Decimal("8.00")


@pytest.mark.parametrize("bad", [True, "1", None, [1]])
def test_type_errors(bad):
    with pytest.raises(TypeError):
        sc(bad, 1, 1, 1, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, bad, 1, 0)
    with pytest.raises(TypeError):
        sc(1, 1, 1, 1, 1, bad)


@pytest.mark.parametrize("args", [
    (0, 1, 1, 1, 1, 0), (1, -1, 1, 1, 1, 0), (1, 1, 0, 1, 1, 0),
    (1, 1, 1, 0, 1, 0), (1, 1, 1, 1, 1, -1),
])
def test_value_errors(args):
    with pytest.raises(ValueError):
        sc(*args)


@pytest.mark.parametrize("zone", [0, 4, True, 1.0, "1", None])
def test_bad_zone(zone):
    with pytest.raises(ValueError):
        sc(1, 1, 1, 1, zone, 0)
