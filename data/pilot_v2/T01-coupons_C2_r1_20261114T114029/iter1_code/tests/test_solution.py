from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 1, 10)


def coupon(**kw):
    c = {"code": "C1", "kind": "percent", "value": D("10"),
         "min_subtotal": D("0"), "expires": TODAY}
    c.update(kw)
    return c


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_shipping_below_and_at_threshold():
    assert order_total([("a", D("99.99"), 1)], None, TODAY, set()) == D("109.99")
    assert order_total([("a", D("50"), 2)], None, TODAY, set()) == D("100.00")


def test_zero_price_item_pays_shipping():
    assert order_total([("a", D("0"), 1)], None, TODAY, set()) == D("10.00")


@pytest.mark.parametrize("qty", [0, -1, 1.5, True])
def test_bad_quantity(qty):
    with pytest.raises(ValueError):
        order_total([("a", D("1"), qty)], None, TODAY, set())


def test_bad_price():
    with pytest.raises(ValueError):
        order_total([("a", D("-0.01"), 1)], None, TODAY, set())


def test_percent():
    # 200 - 20 = 180, free shipping
    assert order_total([("a", D("200"), 1)], coupon(), TODAY, set()) == D("180.00")


def test_shipping_after_discount():
    # 110 - 11 = 99 -> shipping 10
    assert order_total([("a", D("110"), 1)], coupon(), TODAY, set()) == D("109.00")


def test_rounding_half_up():
    assert order_total([("a", D("0.125"), 1)], None, TODAY, set()) == D("10.13")


def test_fixed_and_cap():
    c = coupon(kind="fixed", value=D("30"))
    assert order_total([("a", D("200"), 1)], c, TODAY, set()) == D("170.00")
    c = coupon(kind="fixed", value=D("500"))
    assert order_total([("a", D("20"), 1)], c, TODAY, set()) == D("10.00")


def test_expired_and_boundary():
    c = coupon(expires=date(2024, 1, 9))
    with pytest.raises(CouponError):
        order_total([("a", D("20"), 1)], c, TODAY, set())
    assert order_total([("a", D("20"), 1)], coupon(), TODAY, set()) == D("28.00")


def test_used_code():
    with pytest.raises(CouponError):
        order_total([("a", D("20"), 1)], coupon(), TODAY, {"C1"})


def test_min_subtotal():
    c = coupon(min_subtotal=D("20"))
    assert order_total([("a", D("20"), 1)], c, TODAY, set()) == D("28.00")
    with pytest.raises(CouponError):
        order_total([("a", D("19.99"), 1)], c, TODAY, set())


def test_bad_kind():
    with pytest.raises(CouponError):
        order_total([("a", D("20"), 1)], coupon(kind="x"), TODAY, set())


@pytest.mark.parametrize("v", [D("0"), D("-1"), D("100.01")])
def test_bad_percent(v):
    with pytest.raises(ValueError):
        order_total([("a", D("20"), 1)], coupon(value=v), TODAY, set())


def test_percent_100():
    assert order_total([("a", D("20"), 1)], coupon(value=D("100")), TODAY, set()) == D("10.00")


@pytest.mark.parametrize("v", [D("0"), D("-5")])
def test_bad_fixed(v):
    with pytest.raises(ValueError):
        order_total([("a", D("20"), 1)], coupon(kind="fixed", value=v), TODAY, set())
