from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 5, 10)


def coupon(**kw):
    c = {"code": "C1", "kind": "percent", "value": D("10"),
         "min_subtotal": D("0"), "expires": TODAY}
    c.update(kw)
    return c


def item(price="50", qty=1):
    return [("a", D(price), qty)]


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_empty_with_coupon_zero_min():
    assert order_total([], coupon(), TODAY, set()) == D("0.00")


def test_shipping_below_and_at_100():
    assert order_total(item("99.99"), None, TODAY, set()) == D("109.99")
    assert order_total(item("100"), None, TODAY, set()) == D("100.00")


def test_multiple_items():
    items = [("a", D("10"), 2), ("b", D("5.50"), 3)]
    assert order_total(items, None, TODAY, set()) == D("46.50")


def test_zero_price_ok():
    assert order_total(item("0"), None, TODAY, set()) == D("10.00")


@pytest.mark.parametrize("qty", [0, -1, 1.5, True, "2"])
def test_bad_quantity(qty):
    with pytest.raises(ValueError):
        order_total(item("5", qty), None, TODAY, set())


def test_bad_price():
    with pytest.raises(ValueError):
        order_total(item("-1"), None, TODAY, set())


def test_percent_discount_shipping_after():
    # 110 - 11 = 99 -> shipping 10
    assert order_total(item("110"), coupon(), TODAY, set()) == D("109.00")
    # 200 - 20 = 180 free
    assert order_total(item("200"), coupon(), TODAY, set()) == D("180.00")
    # exactly 100 after discount: free
    assert order_total(item("200"), coupon(value=D("50")), TODAY, set()) == D("100.00")


def test_percent_100():
    assert order_total(item("50"), coupon(value=D("100")), TODAY, set()) == D("10.00")


def test_rounding_half_up():
    # 100.05 * 0.9 ... use 0.05 * 90% = 0.045 -> after 0.005 -> +10 = 10.005 -> 10.01
    assert order_total(item("0.05"), coupon(value=D("90")), TODAY, set()) == D("10.01")


def test_fixed():
    c = coupon(kind="fixed", value=D("30"))
    assert order_total(item("150"), c, TODAY, set()) == D("120.00")
    assert order_total(item("20"), c, TODAY, set()) == D("10.00")


def test_expiry():
    assert order_total(item(), coupon(expires=TODAY), TODAY, set()) == D("55.00")
    with pytest.raises(CouponError):
        order_total(item(), coupon(expires=date(2024, 5, 9)), TODAY, set())


def test_used():
    with pytest.raises(CouponError):
        order_total(item(), coupon(), TODAY, {"C1"})
    assert order_total(item(), coupon(), TODAY, {"X"}) == D("55.00")


def test_min_subtotal():
    assert order_total(item("50"), coupon(min_subtotal=D("50")), TODAY, set()) == D("55.00")
    with pytest.raises(CouponError):
        order_total(item("50"), coupon(min_subtotal=D("50.01")), TODAY, set())


def test_unknown_kind():
    with pytest.raises(CouponError):
        order_total(item(), coupon(kind="bogus", value=D("0")), TODAY, set())


@pytest.mark.parametrize("value", [D("0"), D("-5"), D("100.01")])
def test_bad_percent(value):
    with pytest.raises(ValueError):
        order_total(item(), coupon(value=value), TODAY, set())


@pytest.mark.parametrize("value", [D("0"), D("-5")])
def test_bad_fixed(value):
    with pytest.raises(ValueError):
        order_total(item(), coupon(kind="fixed", value=value), TODAY, set())
