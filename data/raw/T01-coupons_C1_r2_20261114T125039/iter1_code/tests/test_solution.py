from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 5, 10)


def coupon(**kw):
    c = {"code": "C1", "kind": "percent", "value": D("10"), "min_subtotal": D("0"),
         "expires": TODAY}
    c.update(kw)
    return c


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_empty_with_coupon():
    assert order_total([], coupon(), TODAY, set()) == D("0.00")


def test_shipping_and_free():
    assert order_total([("a", D("50"), 1)], None, TODAY, set()) == D("60.00")
    assert order_total([("a", D("50"), 2)], None, TODAY, set()) == D("100.00")
    assert order_total([("a", D("99.99"), 1)], None, TODAY, set()) == D("109.99")


def test_percent_shipping_after_discount():
    items = [("a", D("100"), 1)]
    assert order_total(items, coupon(), TODAY, set()) == D("100.00")
    items = [("a", D("105"), 1)]
    assert order_total(items, coupon(), TODAY, set()) == D("104.50")
    items = [("a", D("100"), 1)]
    assert order_total(items, coupon(value=D("50")), TODAY, set()) == D("60.00")


def test_fixed():
    items = [("a", D("120"), 1)]
    assert order_total(items, coupon(kind="fixed", value=D("30")), TODAY, set()) == D("100.00")
    items = [("a", D("20"), 1)]
    assert order_total(items, coupon(kind="fixed", value=D("500")), TODAY, set()) == D("10.00")


def test_rounding_half_up():
    items = [("a", D("0.05"), 1)]
    assert order_total(items, coupon(value=D("50")), TODAY, set()) == D("10.03")
    items = [("a", D("200.01"), 1)]
    assert order_total(items, coupon(value=D("50")), TODAY, set()) == D("100.01")


def test_invalid_items():
    for bad in [("a", D("1"), 0), ("a", D("1"), -1), ("a", D("1"), 1.5),
                ("a", D("1"), True), ("a", D("-1"), 1)]:
        with pytest.raises(ValueError):
            order_total([bad], None, TODAY, set())


def test_coupon_errors():
    items = [("a", D("50"), 1)]
    with pytest.raises(CouponError):
        order_total(items, coupon(expires=date(2024, 5, 9)), TODAY, set())
    with pytest.raises(CouponError):
        order_total(items, coupon(), TODAY, {"C1"})
    with pytest.raises(CouponError):
        order_total(items, coupon(min_subtotal=D("50.01")), TODAY, set())
    assert order_total(items, coupon(min_subtotal=D("50")), TODAY, set()) == D("55.00")
    with pytest.raises(CouponError):
        order_total(items, coupon(kind="bogus"), TODAY, set())


def test_coupon_value_errors():
    items = [("a", D("50"), 1)]
    for c in [coupon(value=D("0")), coupon(value=D("101")), coupon(kind="fixed", value=D("0")),
              coupon(kind="fixed", value=D("-1"))]:
        with pytest.raises(ValueError):
            order_total(items, c, TODAY, set())
    assert order_total(items, coupon(value=D("100")), TODAY, set()) == D("10.00")
