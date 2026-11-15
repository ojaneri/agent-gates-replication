from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 5, 1)


def coupon(**kw):
    c = {"code": "C1", "kind": "percent", "value": D("10"), "min_subtotal": D("0"),
         "expires": TODAY}
    c.update(kw)
    return c


def test_no_coupon_shipping():
    assert order_total([("a", D("20"), 2)], None, TODAY, set()) == D("50.00")


def test_free_shipping_at_100():
    assert order_total([("a", D("100"), 1)], None, TODAY, set()) == D("100.00")


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_invalid_items():
    for q in (0, -1, 1.5, True):
        with pytest.raises(ValueError):
            order_total([("a", D("1"), q)], None, TODAY, set())
    with pytest.raises(ValueError):
        order_total([("a", D("-1"), 1)], None, TODAY, set())


def test_percent_and_shipping_after_discount():
    # 110 - 10% = 99 -> shipping 10
    assert order_total([("a", D("110"), 1)], coupon(), TODAY, set()) == D("109.00")
    assert order_total([("a", D("200"), 1)], coupon(), TODAY, set()) == D("180.00")


def test_rounding_half_up():
    assert order_total([("a", D("100.05"), 1)], coupon(value=D("0.5")), TODAY, set()) == D("109.55")
    assert order_total([("a", D("0.05"), 1)], coupon(value=D("50")), TODAY, set()) == D("10.03")


def test_fixed_capped():
    c = coupon(kind="fixed", value=D("500"))
    assert order_total([("a", D("20"), 1)], c, TODAY, set()) == D("10.00")
    c = coupon(kind="fixed", value=D("5"))
    assert order_total([("a", D("20"), 1)], c, TODAY, set()) == D("25.00")


def test_coupon_errors():
    items = [("a", D("50"), 1)]
    with pytest.raises(CouponError):
        order_total(items, coupon(expires=date(2024, 4, 30)), TODAY, set())
    order_total(items, coupon(), TODAY, set())  # expiry day ok
    with pytest.raises(CouponError):
        order_total(items, coupon(), TODAY, {"C1"})
    with pytest.raises(CouponError):
        order_total(items, coupon(min_subtotal=D("50.01")), TODAY, set())
    order_total(items, coupon(min_subtotal=D("50")), TODAY, set())
    with pytest.raises(CouponError):
        order_total(items, coupon(kind="bogus"), TODAY, set())


def test_value_errors():
    items = [("a", D("50"), 1)]
    for v in (D("0"), D("101"), D("-1")):
        with pytest.raises(ValueError):
            order_total(items, coupon(value=v), TODAY, set())
    assert order_total(items, coupon(value=D("100")), TODAY, set()) == D("10.00")
    for v in (D("0"), D("-1")):
        with pytest.raises(ValueError):
            order_total(items, coupon(kind="fixed", value=v), TODAY, set())
