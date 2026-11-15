from decimal import Decimal

import pytest

from solution import shipping_cost


def c(l=10, w=10, h=10, kg=1, zone=1, sub=0):
    return shipping_cost(l, w, h, kg, zone, sub)


def test_base_weights():
    assert c(kg=0.5) == Decimal("8.00")
    assert c(kg=1) == Decimal("8.00")
    assert c(kg=1.01) == Decimal("9.50")
    assert c(kg=1.5) == Decimal("9.50")
    assert c(kg=2) == Decimal("11.00")


def test_result_type_and_places():
    r = c()
    assert isinstance(r, Decimal)
    assert str(r) == "8.00"


def test_volumetric():
    # 50*40*30/5000 = 12 kg -> 8 + 1.5*22
    assert c(50, 40, 30, 1) == Decimal("41.00")


def test_zones():
    assert c(zone=2) == Decimal("10.00")
    assert c(zone=3) == Decimal("12.80")


def test_free_shipping():
    assert c(sub=150, zone=1) == Decimal("0.00")
    assert c(sub=150, zone=2) == Decimal("0.00")
    assert c(sub=149.99, zone=2) == Decimal("10.00")
    assert c(sub=500, zone=3) == Decimal("12.80")


def test_oversize():
    assert c(l=120, w=1, h=1, kg=1) == Decimal("8.00")
    assert c(l=121, w=1, h=1, kg=1) == Decimal("20.00")
    assert c(l=121, w=1, h=1, kg=1, zone=3) == Decimal("24.80")
    assert c(l=121, w=1, h=1, kg=1, sub=200) == Decimal("12.00")


def test_rounding_half_up():
    assert c(kg=1.5, zone=2, sub=0) == Decimal("11.88")  # 11.875
    assert c(Decimal("10"), 10, 10, Decimal("1")) == Decimal("8.00")


@pytest.mark.parametrize("bad", ["1", None, True, [1]])
def test_type_errors(bad):
    with pytest.raises(TypeError):
        shipping_cost(bad, 1, 1, 1, 1, 0)
    with pytest.raises(TypeError):
        shipping_cost(1, 1, 1, 1, 1, bad)


@pytest.mark.parametrize("args", [
    (0, 1, 1, 1, 1, 0), (1, -1, 1, 1, 1, 0), (1, 1, 0, 1, 1, 0),
    (1, 1, 1, 0, 1, 0), (1, 1, 1, 1, 1, -1), (1, 1, 1, float("nan"), 1, 0),
    (1, 1, 1, 1, 0, 0), (1, 1, 1, 1, 4, 0), (1, 1, 1, 1, True, 0),
    (1, 1, 1, 1, 1.0, 0), (1, 1, 1, 1, "1", 0),
])
def test_value_errors(args):
    with pytest.raises(ValueError):
        shipping_cost(*args)
