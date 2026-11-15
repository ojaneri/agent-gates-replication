from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 15)
D = Decimal


def coupon(kind="percent", value=D("10"), min_subtotal=D("0"), expires=date(2026, 12, 31),
           code="SAVE"):
    return {"code": code, "kind": kind, "value": value,
            "min_subtotal": min_subtotal, "expires": expires}


def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_small_order_pays_shipping():
    items = [("A", D("20.00"), 2)]
    assert order_total(items, None, TODAY, set()) == D("50.00")


def test_order_at_100_ships_free():
    items = [("A", D("50.00"), 2)]
    assert order_total(items, None, TODAY, set()) == D("100.00")


def test_just_below_100_pays_shipping():
    items = [("A", D("99.99"), 1)]
    assert order_total(items, None, TODAY, set()) == D("109.99")


def test_subtotal_sums_quantities():
    items = [("A", D("1.10"), 3), ("B", D("2.25"), 4)]
    # subtotal 3.30 + 9.00 = 12.30, plus shipping 10.00
    assert order_total(items, None, TODAY, set()) == D("22.30")


def test_percent_discount_then_shipping_threshold_uses_discounted_subtotal():
    # 110 subtotal, 10% off -> 99.00 -> shipping applies
    items = [("A", D("110.00"), 1)]
    assert order_total(items, coupon("percent", D("10")), TODAY, set()) == D("109.00")


def test_percent_discount_free_shipping_when_discounted_at_100():
    # 111.11 * 0.9 = 99.999 -> not free; use 200 at 50% -> 100 -> free
    items = [("A", D("200.00"), 1)]
    assert order_total(items, coupon("percent", D("50")), TODAY, set()) == D("100.00")


def test_fixed_discount():
    items = [("A", D("60.00"), 1)]
    # 60 - 15 = 45, shipping 10
    assert order_total(items, coupon("fixed", D("15")), TODAY, set()) == D("55.00")


def test_fixed_discount_capped_at_subtotal():
    items = [("A", D("5.00"), 1)]
    # discount capped at 5 -> 0 after discount, shipping 10
    assert order_total(items, coupon("fixed", D("50")), TODAY, set()) == D("10.00")


def test_rounding_half_up():
    # subtotal 0.05, 50% off -> discount 0.025 -> after 0.025 -> + shipping 10 -> 10.025 -> 10.03
    items = [("A", D("0.05"), 1)]
    assert order_total(items, coupon("percent", D("50")), TODAY, set()) == D("10.03")


def test_expiry_date_is_inclusive():
    items = [("A", D("200.00"), 1)]
    c = coupon("percent", D("10"), expires=TODAY)
    assert order_total(items, c, TODAY, set()) == D("180.00")


def test_expired_coupon_raises():
    items = [("A", D("200.00"), 1)]
    c = coupon("percent", D("10"), expires=date(2026, 6, 14))
    with pytest.raises(CouponError):
        order_total(items, c, TODAY, set())


def test_used_coupon_raises():
    items = [("A", D("200.00"), 1)]
    with pytest.raises(CouponError):
        order_total(items, coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_codes_do_not_block():
    items = [("A", D("200.00"), 1)]
    assert order_total(items, coupon(code="SAVE"), TODAY, {"OTHER"}) == D("180.00")


def test_min_subtotal_equal_is_accepted():
    items = [("A", D("50.00"), 2)]
    c = coupon("percent", D("10"), min_subtotal=D("100.00"))
    assert order_total(items, c, TODAY, set()) == D("100.00")


def test_below_min_subtotal_raises():
    items = [("A", D("49.99"), 2)]
    c = coupon("percent", D("10"), min_subtotal=D("100.00"))
    with pytest.raises(CouponError):
        order_total(items, c, TODAY, set())


def test_unknown_kind_raises_coupon_error():
    items = [("A", D("200.00"), 1)]
    with pytest.raises(CouponError):
        order_total(items, coupon("bogus"), TODAY, set())


@pytest.mark.parametrize("value", [D("0"), D("-1"), D("100.01")])
def test_invalid_percent_value_raises_value_error(value):
    items = [("A", D("200.00"), 1)]
    with pytest.raises(ValueError):
        order_total(items, coupon("percent", value), TODAY, set())


def test_percent_100_is_allowed():
    # Discounted subtotal is 0, which is below 100.00, so shipping still applies.
    items = [("A", D("200.00"), 1)]
    assert order_total(items, coupon("percent", D("100")), TODAY, set()) == D("10.00")


@pytest.mark.parametrize("value", [D("0"), D("-5")])
def test_invalid_fixed_value_raises_value_error(value):
    items = [("A", D("200.00"), 1)]
    with pytest.raises(ValueError):
        order_total(items, coupon("fixed", value), TODAY, set())


@pytest.mark.parametrize("qty", [0, -1, 1.5, "2"])
def test_invalid_quantity_raises_value_error(qty):
    items = [("A", D("1.00"), qty)]
    with pytest.raises(ValueError):
        order_total(items, None, TODAY, set())


def test_negative_price_raises_value_error():
    items = [("A", D("-0.01"), 1)]
    with pytest.raises(ValueError):
        order_total(items, None, TODAY, set())


def test_zero_price_is_allowed():
    items = [("A", D("0"), 1)]
    assert order_total(items, None, TODAY, set()) == D("10.00")
