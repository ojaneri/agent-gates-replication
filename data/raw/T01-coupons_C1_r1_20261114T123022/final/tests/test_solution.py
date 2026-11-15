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


def test_free_shipping_boundary():
    assert order_total([("a", D("100"), 1)], None, TODAY, set()) == D("100.00")
    assert order_total([("a", D("99.99"), 1)], None, TODAY, set()) == D("109.99")


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")
    assert order_total([], coupon(), TODAY, set()) == D("0.00")


@pytest.mark.parametrize("item", [("a", D("1"), 0), ("a", D("1"), -1), ("a", D("1"), 1.5),
                                  ("a", D("1"), True), ("a", D("-1"), 1)])
def test_invalid_items(item):
    with pytest.raises(ValueError):
        order_total([item], None, TODAY, set())


def test_percent_shipping_after_discount():
    # 120 - 10% = 108 -> free shipping
    assert order_total([("a", D("120"), 1)], coupon(), TODAY, set()) == D("108.00")
    # 110 - 10% = 99 -> shipping
    assert order_total([("a", D("110"), 1)], coupon(), TODAY, set()) == D("109.00")


def test_rounding_half_up():
    assert order_total([("a", D("100.05"), 1)], coupon(value=D("50")), TODAY,
                       set()) == D("60.03")  # 50.025 + 10 = 60.025
    assert order_total([("a", D("0.05"), 1)], coupon(value=D("50")), TODAY,
                       set()) == D("10.03")


def test_fixed():
    c = coupon(kind="fixed", value=D("30"))
    assert order_total([("a", D("200"), 1)], c, TODAY, set()) == D("170.00")
    c = coupon(kind="fixed", value=D("500"))
    assert order_total([("a", D("20"), 1)], c, TODAY, set()) == D("10.00")


def test_coupon_errors():
    items = [("a", D("50"), 1)]
    with pytest.raises(CouponError):
        order_total(items, coupon(expires=date(2024, 4, 30)), TODAY, set())
    with pytest.raises(CouponError):
        order_total(items, coupon(), TODAY, {"C1"})
    with pytest.raises(CouponError):
        order_total(items, coupon(min_subtotal=D("50.01")), TODAY, set())
    with pytest.raises(CouponError):
        order_total(items, coupon(kind="bogus"), TODAY, set())
    assert order_total(items, coupon(min_subtotal=D("50")), TODAY, set()) == D("55.00")


@pytest.mark.parametrize("c", [coupon(value=D("0")), coupon(value=D("101")),
                               coupon(kind="fixed", value=D("0")),
                               coupon(kind="fixed", value=D("-5"))])
def test_bad_values(c):
    with pytest.raises(ValueError):
        order_total([("a", D("50"), 1)], c, TODAY, set())


def test_percent_100():
    assert order_total([("a", D("50"), 1)], coupon(value=D("100")), TODAY,
                       set()) == D("10.00")
