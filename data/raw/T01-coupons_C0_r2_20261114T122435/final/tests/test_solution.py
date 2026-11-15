from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 5, 10)


def c(**kw):
    base = dict(code="C1", kind="percent", value=D("10"), min_subtotal=D("0"),
                expires=TODAY)
    base.update(kw)
    return base


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_shipping_below_and_at_threshold():
    assert order_total([("a", D("99.99"), 1)], None, TODAY, set()) == D("109.99")
    assert order_total([("a", D("100.00"), 1)], None, TODAY, set()) == D("100.00")


def test_invalid_items():
    for items in ([("a", D("1"), 0)], [("a", D("1"), -1)], [("a", D("1"), 1.5)],
                  [("a", D("-1"), 1)]):
        with pytest.raises(ValueError):
            order_total(items, None, TODAY, set())


def test_percent_and_shipping_after_discount():
    items = [("a", D("100"), 1)]
    assert order_total(items, c(), TODAY, set()) == D("100.00")  # 90 + 10
    assert order_total(items, c(value=D("100")), TODAY, set()) == D("10.00")


def test_fixed_capped():
    items = [("a", D("50"), 1)]
    assert order_total(items, c(kind="fixed", value=D("500")), TODAY, set()) == D("10.00")
    assert order_total([("a", D("200"), 1)], c(kind="fixed", value=D("20")), TODAY,
                       set()) == D("180.00")


def test_rounding_half_up():
    assert order_total([("a", D("100.005"), 1)], None, TODAY, set()) == D("100.01")


def test_coupon_errors():
    items = [("a", D("100"), 1)]
    with pytest.raises(CouponError):
        order_total(items, c(expires=date(2024, 5, 9)), TODAY, set())
    with pytest.raises(CouponError):
        order_total(items, c(), TODAY, {"C1"})
    with pytest.raises(CouponError):
        order_total(items, c(min_subtotal=D("100.01")), TODAY, set())
    assert order_total(items, c(min_subtotal=D("100")), TODAY, set()) == D("100.00")
    with pytest.raises(CouponError):
        order_total(items, c(kind="bogus"), TODAY, set())


def test_value_errors():
    items = [("a", D("100"), 1)]
    for cp in (c(value=D("0")), c(value=D("101")), c(kind="fixed", value=D("0")),
               c(kind="fixed", value=D("-1"))):
        with pytest.raises(ValueError):
            order_total(items, cp, TODAY, set())
