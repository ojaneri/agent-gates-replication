from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 15)
FUTURE = date(2027, 1, 1)
D = Decimal


def coupon(kind="percent", value=D("10"), min_subtotal=D("0"), expires=FUTURE, code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": value,
        "min_subtotal": min_subtotal,
        "expires": expires,
    }


def one(price, qty=1):
    return [("SKU", D(price), qty)]


# --- basic totals and shipping -------------------------------------------

def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_returns_decimal():
    assert isinstance(order_total(one("5.00"), None, TODAY, set()), Decimal)


def test_below_threshold_pays_shipping():
    assert order_total(one("50.00"), None, TODAY, set()) == D("60.00")


def test_just_below_threshold_pays_shipping():
    assert order_total(one("99.99"), None, TODAY, set()) == D("109.99")


def test_exactly_threshold_is_free_shipping():
    assert order_total(one("100.00"), None, TODAY, set()) == D("100.00")


def test_above_threshold_is_free_shipping():
    assert order_total(one("150.00"), None, TODAY, set()) == D("150.00")


def test_quantity_multiplies_price():
    assert order_total(one("25.00", 4), None, TODAY, set()) == D("100.00")


def test_sums_multiple_items():
    items = [("A", D("30.00"), 2), ("B", D("20.00"), 1)]
    assert order_total(items, None, TODAY, set()) == D("80.00") + D("10.00")


def test_zero_price_item_still_pays_shipping():
    assert order_total(one("0.00"), None, TODAY, set()) == D("10.00")


# --- input validation ------------------------------------------------------

@pytest.mark.parametrize("qty", [0, -1, 1.0, True])
def test_invalid_quantity_raises(qty):
    with pytest.raises(ValueError):
        order_total([("SKU", D("5.00"), qty)], None, TODAY, set())


def test_negative_price_raises():
    with pytest.raises(ValueError):
        order_total(one("-0.01"), None, TODAY, set())


def test_zero_price_is_accepted_as_valid_input():
    assert order_total(one("0"), None, TODAY, set()) == D("10.00")


def test_validation_happens_before_coupon_checks():
    with pytest.raises(ValueError):
        order_total([("SKU", D("5.00"), 0)], coupon(code="X"), TODAY, {"X"})


# --- coupon validity ---------------------------------------------------------

def test_coupon_valid_on_expiry_date():
    # 100 - 10% = 90 -> shipping charged.
    result = order_total(one("100.00"), coupon(expires=TODAY), TODAY, set())
    assert result == D("100.00")


def test_coupon_expired_the_day_after_raises():
    with pytest.raises(CouponError):
        order_total(one("100.00"), coupon(expires=date(2026, 6, 14)), TODAY, set())


def test_used_code_raises():
    with pytest.raises(CouponError):
        order_total(one("100.00"), coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_code_does_not_block():
    result = order_total(one("100.00"), coupon(code="SAVE"), TODAY, {"OTHER"})
    assert result == D("100.00")


def test_subtotal_equal_to_minimum_is_accepted():
    result = order_total(one("50.00"), coupon(min_subtotal=D("50.00")), TODAY, set())
    assert result == D("45.00") + D("10.00")


def test_subtotal_below_minimum_raises():
    with pytest.raises(CouponError):
        order_total(one("49.99"), coupon(min_subtotal=D("50.00")), TODAY, set())


def test_unknown_kind_raises_coupon_error():
    with pytest.raises(CouponError):
        order_total(one("100.00"), coupon(kind="bogus"), TODAY, set())


def test_empty_order_below_positive_minimum_raises():
    with pytest.raises(CouponError):
        order_total([], coupon(min_subtotal=D("1.00")), TODAY, set())


def test_empty_order_with_zero_minimum_is_zero():
    assert order_total([], coupon(min_subtotal=D("0")), TODAY, set()) == D("0.00")


def test_coupon_error_is_a_value_error():
    assert issubclass(CouponError, ValueError)


# --- percent coupons ---------------------------------------------------------

def test_percent_discount_then_free_shipping():
    assert order_total(one("200.00"), coupon(value=D("10")), TODAY, set()) == D("180.00")


def test_percent_discount_applies_before_shipping_threshold():
    # 120 * 0.8 = 96 -> below 100 after discount, so shipping is charged.
    assert order_total(one("120.00"), coupon(value=D("20")), TODAY, set()) == D("106.00")


def test_percent_100_leaves_only_shipping():
    assert order_total(one("50.00"), coupon(value=D("100")), TODAY, set()) == D("10.00")


@pytest.mark.parametrize("value", [D("0"), D("-5"), D("100.01"), D("150")])
def test_percent_out_of_range_raises(value):
    with pytest.raises(ValueError):
        order_total(one("100.00"), coupon(value=value), TODAY, set())


def test_percent_value_checked_after_validity():
    with pytest.raises(CouponError):
        order_total(one("100.00"), coupon(value=D("0"), expires=date(2000, 1, 1)),
                    TODAY, set())


# --- fixed coupons -----------------------------------------------------------

def test_fixed_discount_subtracted():
    assert order_total(one("50.00"), coupon(kind="fixed", value=D("30")), TODAY, set()) == D("30.00")


def test_fixed_discount_capped_at_subtotal():
    assert order_total(one("50.00"), coupon(kind="fixed", value=D("80")), TODAY, set()) == D("10.00")


def test_fixed_discount_equal_to_subtotal():
    assert order_total(one("50.00"), coupon(kind="fixed", value=D("50")), TODAY, set()) == D("10.00")


def test_fixed_discount_can_drop_below_threshold_into_shipping():
    # 105 - 10 = 95 -> shipping charged.
    assert order_total(one("105.00"), coupon(kind="fixed", value=D("10")), TODAY, set()) == D("105.00")


@pytest.mark.parametrize("value", [D("0"), D("-1")])
def test_fixed_non_positive_value_raises(value):
    with pytest.raises(ValueError):
        order_total(one("100.00"), coupon(kind="fixed", value=value), TODAY, set())


def test_fixed_value_on_empty_order_is_zero():
    assert order_total([], coupon(kind="fixed", value=D("5")), TODAY, set()) == D("0.00")


# --- rounding ----------------------------------------------------------------

def test_half_rounds_up():
    assert order_total(one("100.005"), None, TODAY, set()) == D("100.01")


def test_below_half_rounds_down():
    assert order_total(one("100.004"), None, TODAY, set()) == D("100.00")


def test_percent_result_rounded_half_up():
    # 1.05 - 10% (0.105) = 0.945 net, shipping 10 -> 10.945 -> 10.95
    result = order_total(one("1.05"), coupon(value=D("10")), TODAY, set())
    assert result == D("10.95")
