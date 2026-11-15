from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

T = date(2025, 1, 10)


def c(**kw):
    d = dict(code="X", kind="percent", value=D("10"), min_subtotal=D("0"), expires=T)
    d.update(kw)
    return d


def test_empty():
    assert order_total([], None, T, set()) == D("0.00")


def test_shipping():
    assert order_total([("a", D("50"), 1)], None, T, set()) == D("60.00")
    assert order_total([("a", D("50"), 2)], None, T, set()) == D("100.00")


def test_percent_and_shipping_after_discount():
    # 100 - 10 = 90 -> shipping applies
    assert order_total([("a", D("100"), 1)], c(), T, set()) == D("100.00")


def test_fixed_capped():
    assert order_total([("a", D("5"), 1)], c(kind="fixed", value=D("50")), T, set()) == D("10.00")


def test_rounding_half_up():
    assert order_total([("a", D("0.05"), 1)], c(value=D("50")), T, set()) == D("10.03")


def test_invalid_items():
    for items in ([("a", D("1"), 0)], [("a", D("1"), 1.5)], [("a", D("-1"), 1)]):
        with pytest.raises(ValueError):
            order_total(items, None, T, set())


def test_coupon_errors():
    it = [("a", D("50"), 1)]
    with pytest.raises(CouponError):
        order_total(it, c(expires=date(2025, 1, 9)), T, set())
    with pytest.raises(CouponError):
        order_total(it, c(), T, {"X"})
    with pytest.raises(CouponError):
        order_total(it, c(min_subtotal=D("50.01")), T, set())
    with pytest.raises(CouponError):
        order_total(it, c(kind="bogus"), T, set())
    assert order_total(it, c(min_subtotal=D("50")), T, set()) == D("55.00")


def test_value_errors():
    it = [("a", D("50"), 1)]
    for cp in (c(value=D("0")), c(value=D("101")), c(kind="fixed", value=D("0"))):
        with pytest.raises(ValueError):
            order_total(it, cp, T, set())
