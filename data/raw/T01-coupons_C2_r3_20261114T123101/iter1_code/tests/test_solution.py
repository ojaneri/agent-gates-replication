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


def items(price="50", qty=2):
    return [("a", D(price), qty)]


def test_no_coupon_free_shipping():
    assert order_total(items("50", 2), None, TODAY, set()) == D("100.00")


def test_shipping_below_100():
    assert order_total(items("49.99", 2), None, TODAY, set()) == D("109.98")


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_empty_with_coupon_zero_min():
    assert order_total([], coupon(), TODAY, set()) == D("0.00")


def test_invalid_quantity():
    for q in (0, -1, 1.5, True):
        with pytest.raises(ValueError):
            order_total([("a", D("1"), q)], None, TODAY, set())


def test_negative_price():
    with pytest.raises(ValueError):
        order_total([("a", D("-1"), 1)], None, TODAY, set())


def test_zero_price_ok():
    assert order_total([("a", D("0"), 1)], None, TODAY, set()) == D("10.00")


def test_percent_discount_and_shipping_after_discount():
    # 120 - 10% = 108 -> free shipping
    assert order_total(items("60", 2), coupon(), TODAY, set()) == D("108.00")
    # 110 - 10% = 99 -> shipping
    assert order_total(items("110", 1), coupon(), TODAY, set()) == D("109.00")


def test_shipping_boundary_exactly_100():
    assert order_total(items("100", 1), coupon(value=D("0.5")), TODAY, set()) == D("99.50") + D("10")
    assert order_total(items("200", 1), coupon(value=D("50")), TODAY, set()) == D("100.00")


def test_percent_100():
    assert order_total(items("20", 1), coupon(value=D("100")), TODAY, set()) == D("10.00")


def test_percent_invalid_values():
    for v in (D("0"), D("-1"), D("100.01")):
        with pytest.raises(ValueError):
            order_total(items(), coupon(value=v), TODAY, set())


def test_fixed():
    c = coupon(kind="fixed", value=D("20"))
    assert order_total(items("100", 2), c, TODAY, set()) == D("180.00")


def test_fixed_capped_at_subtotal():
    c = coupon(kind="fixed", value=D("500"))
    assert order_total(items("30", 1), c, TODAY, set()) == D("10.00")


def test_fixed_invalid():
    for v in (D("0"), D("-5")):
        with pytest.raises(ValueError):
            order_total(items(), coupon(kind="fixed", value=v), TODAY, set())


def test_expired_and_boundary():
    with pytest.raises(CouponError):
        order_total(items(), coupon(expires=date(2024, 5, 9)), TODAY, set())
    order_total(items(), coupon(expires=TODAY), TODAY, set())


def test_used_code():
    with pytest.raises(CouponError):
        order_total(items(), coupon(), TODAY, {"C1"})
    order_total(items(), coupon(), TODAY, {"other"})


def test_min_subtotal():
    with pytest.raises(CouponError):
        order_total(items("50", 2), coupon(min_subtotal=D("100.01")), TODAY, set())
    order_total(items("50", 2), coupon(min_subtotal=D("100")), TODAY, set())


def test_bad_kind():
    with pytest.raises(CouponError):
        order_total(items(), coupon(kind="bogus"), TODAY, set())


def test_rounding_half_up():
    # 10.05 * 5% = 0.5025 ; 10.05 - 0.5025 = 9.5475 + 10 = 19.5475 -> 19.55
    assert order_total([("a", D("10.05"), 1)], coupon(value=D("5")), TODAY, set()) == D("19.55")
    # 0.125 -> 0.13 (no coupon: 0.125 + 10 = 10.125 -> 10.13)
    assert order_total([("a", D("0.125"), 1)], None, TODAY, set()) == D("10.13")


def test_coupon_error_is_value_error():
    assert issubclass(CouponError, ValueError)
