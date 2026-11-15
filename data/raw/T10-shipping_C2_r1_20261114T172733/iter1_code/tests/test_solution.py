from decimal import Decimal

import pytest

from solution import shipping_cost


def c(l=10, w=10, h=10, kg=1, zone=1, sub=0):
    return shipping_cost(l, w, h, kg, zone, sub)


def test_basic_weights():
    assert c(kg=0.5) == Decimal("8.00")
    assert c(kg=1) == Decimal("8.00")
    assert c(kg=1.01) == Decimal("9.50")
    assert c(kg=1.5) == Decimal("9.50")
    assert c(kg=2) == Decimal("11.00")
    assert c(kg=2.1) == Decimal("12.50")


def test_result_type_and_places():
    r = c()
    assert isinstance(r, Decimal)
    assert str(r) == "8.00"


def test_volumetric():
    assert c(50, 40, 25, 1) == Decimal("8.00") + Decimal("1.5") * 18


def test_volumetric_exact_multiple():
    assert c(50, 50, 10, 1) == Decimal("20.00")
    assert c(50, 50, 10.1, 1) == Decimal("21.50")


def test_zones():
    assert c(zone=2) == Decimal("10.00")
    assert c(zone=3) == Decimal("12.80")
    assert c(kg=1.5, zone=2) == Decimal("11.88")
    assert c(kg=1.5, zone=3) == Decimal("15.20")


def test_free_shipping():
    assert c(zone=1, sub=150) == Decimal("0.00")
    assert c(zone=2, sub=150) == Decimal("0.00")
    assert c(zone=1, sub=149.99) == Decimal("8.00")
    assert c(zone=3, sub=500) == Decimal("12.80")


def test_oversize():
    assert c(120, 1, 1) == Decimal("8.00")
    assert c(121, 1, 1, kg=1) == Decimal("20.00")
    assert c(1, 121, 1) == Decimal("20.00")
    assert c(1, 1, 121) == Decimal("20.00")
    assert c(121, 1, 1, zone=3) == Decimal("24.80")
    assert c(121, 1, 1, zone=1, sub=200) == Decimal("12.00")


def test_rounding_half_up():
    assert c(kg=1.5, zone=2, sub=0) == Decimal("11.88")
    assert c(kg=Decimal("1"), zone=3, sub=0) == Decimal("12.80")


def test_types():
    assert c(Decimal("10"), 10, 10, Decimal("0.1")) == Decimal("8.00")
    for bad in ("1", None, True):
        with pytest.raises(TypeError):
            c(l=bad)
        with pytest.raises(TypeError):
            c(kg=bad)
        with pytest.raises(TypeError):
            c(sub=bad)


def test_values():
    for kw in ({"l": 0}, {"w": -1}, {"h": 0}, {"kg": 0}, {"sub": -1},
               {"kg": float("nan")}, {"kg": float("inf")}):
        with pytest.raises(ValueError):
            c(**kw)
    assert c(sub=0) == Decimal("8.00")


def test_zone_invalid():
    for z in (0, 4, True, 1.0, "1", None):
        with pytest.raises(ValueError):
            c(zone=z)
