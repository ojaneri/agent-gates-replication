from decimal import Decimal

import pytest

from solution import shipping_cost as sc


def test_basic_weights():
    assert sc(10, 10, 10, 0.5, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1, 1, 0) == Decimal("8.00")
    assert sc(10, 10, 10, 1.01, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 1.5, 1, 0) == Decimal("9.50")
    assert sc(10, 10, 10, 2, 1, 0) == Decimal("11.00")


def test_result_type_and_places():
    r = sc(10, 10, 10, 1, 1, 0)
    assert isinstance(r, Decimal)
    assert str(r) == "8.00"


def test_volumetric():
    # 50*50*20/5000 = 10kg -> 8 + 1.5*18 = 35
    assert sc(50, 50, 20, 1, 1, 0) == Decimal("35.00")


def test_zones():
    assert sc(10, 10, 10, 1, 2, 0) == Decimal("10.00")
    assert sc(10, 10, 10, 1, 3, 0) == Decimal("12.80")
    assert sc(10, 10, 10, 1.5, 2, 0) == Decimal("11.875").quantize(Decimal("0.01"), "ROUND_HALF_UP")


def test_free_shipping():
    assert sc(10, 10, 10, 1, 1, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 2, 150) == Decimal("0.00")
    assert sc(10, 10, 10, 1, 3, 150) == Decimal("12.80")
    assert sc(10, 10, 10, 1, 1, Decimal("149.99")) == Decimal("8.00")


def test_oversize():
    assert sc(120, 5, 5, 1, 1, 0) == Decimal("8.00")
    assert sc(121, 1, 1, 1, 1, 0) == Decimal("20.00")
    assert sc(1, 121, 1, 1, 3, 0) == Decimal("24.80")
    assert sc(1, 1, 121, 1, 1, 200) == Decimal("12.00")


def test_float_and_decimal_inputs():
    assert sc(Decimal("10"), 10.0, 10, Decimal("0.1"), 1, 0.0) == Decimal("8.00")
    assert sc(10, 10, 10, 1.0, 1, 0) == Decimal("8.00")


def test_type_errors():
    for args in [
        (True, 1, 1, 1, 1, 0),
        ("1", 1, 1, 1, 1, 0),
        (1, 1, 1, None, 1, 0),
        (1, 1, 1, 1, 1, True),
        (1, 1, 1, 1, 1, "0"),
    ]:
        with pytest.raises(TypeError):
            sc(*args)


def test_value_errors():
    for args in [
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
    ]:
        with pytest.raises(ValueError):
            sc(*args)
