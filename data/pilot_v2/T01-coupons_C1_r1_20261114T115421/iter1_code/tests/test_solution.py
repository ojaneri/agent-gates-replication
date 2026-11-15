from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 15)
FUTURE = date(2027, 1, 1)
PAST = date(2026, 6, 14)


def coupon(kind="percent", value="10", min_subtotal="0", expires=FUTURE, code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": Decimal(value),
        "min_subtotal": Decimal(min_subtotal),
        "expires": expires,
    }


def items_for(subtotal_str):
    return [("sku", Decimal(subtotal_str), 1)]


# --- basic totals and shipping ---------------------------------------------

def test_empty_order_has_no_shipping_and_zero_total():
    assert order_total([], None, TODAY, set()) == Decimal("0.00")


def test_empty_order_with_coupon_min_zero_has_no_shipping():
    assert order_total([], coupon(min_subtotal="0"), TODAY, set()) == Decimal("0.00")


def test_subtotal_sums_unit_price_times_quantity():
    items = [("a", Decimal("10.00"), 3), ("b", Decimal("2.50"), 2)]
    # subtotal 35.00 < 100 -> shipping 10.00
    assert order_total(items, None, TODAY, set()) == Decimal("45.00")


def test_zero_price_item_still_pays_shipping():
    assert order_total([("free", Decimal("0"), 1)], None, TODAY, set()) == Decimal("10.00")


def test_shipping_below_threshold_costs_ten():
    assert order_total(items_for("99.99"), None, TODAY, set()) == Decimal("109.99")


def test_shipping_free_at_exactly_one_hundred():
    assert order_total(items_for("100.00"), None, TODAY, set()) == Decimal("100.00")


def test_shipping_free_above_threshold():
    assert order_total(items_for("250.00"), None, TODAY, set()) == Decimal("250.00")


def test_shipping_computed_after_discount():
    # 110.00 subtotal, 10% off -> 99.00 -> shipping applies
    c = coupon(kind="percent", value="10")
    assert order_total(items_for("110.00"), c, TODAY, set()) == Decimal("109.00")


def test_shipping_free_when_discount_brings_below_threshold_stays_charged():
    # 200 subtotal, 50% off -> 100.00 -> free shipping (exactly at threshold)
    c = coupon(kind="percent", value="50")
    assert order_total(items_for("200.00"), c, TODAY, set()) == Decimal("100.00")


# --- item validation --------------------------------------------------------

@pytest.mark.parametrize("qty", [0, -1, 1.0, "2", None, True])
def test_invalid_quantity_raises_value_error(qty):
    with pytest.raises(ValueError):
        order_total([("sku", Decimal("1.00"), qty)], None, TODAY, set())


def test_negative_unit_price_raises_value_error():
    with pytest.raises(ValueError):
        order_total([("sku", Decimal("-0.01"), 1)], None, TODAY, set())


# --- coupon validity --------------------------------------------------------

def test_coupon_valid_on_expiry_date():
    c = coupon(expires=TODAY)
    # 10% off 100.00 -> 90.00 after discount -> shipping 10.00 -> 100.00
    assert order_total(items_for("100.00"), c, TODAY, set()) == Decimal("100.00")


def test_expired_coupon_raises():
    with pytest.raises(CouponError):
        order_total(items_for("100.00"), coupon(expires=PAST), TODAY, set())


def test_used_coupon_raises():
    with pytest.raises(CouponError):
        order_total(items_for("100.00"), coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_codes_do_not_block():
    assert order_total(items_for("100.00"), coupon(code="SAVE"), TODAY, {"OTHER"}) == Decimal("100.00")


def test_subtotal_equal_to_minimum_is_accepted():
    c = coupon(min_subtotal="50.00", value="0.01")
    # 50.00 - 0.005? percent 0.01 -> discount 0.005 -> 49.995 + 10 = 59.995 -> 60.00
    assert order_total(items_for("50.00"), c, TODAY, set()) == Decimal("60.00")


def test_subtotal_below_minimum_raises():
    with pytest.raises(CouponError):
        order_total(items_for("49.99"), coupon(min_subtotal="50.00"), TODAY, set())


def test_unknown_kind_raises_coupon_error():
    with pytest.raises(CouponError):
        order_total(items_for("100.00"), coupon(kind="bogus"), TODAY, set())


# --- percent coupons --------------------------------------------------------

def test_percent_discount_applied():
    c = coupon(kind="percent", value="12.5")
    # 200 * 12.5% = 25 -> 175, free shipping
    assert order_total(items_for("200.00"), c, TODAY, set()) == Decimal("175.00")


def test_percent_value_100_gives_only_shipping():
    c = coupon(kind="percent", value="100")
    assert order_total(items_for("80.00"), c, TODAY, set()) == Decimal("10.00")


@pytest.mark.parametrize("value", ["0", "-5", "100.01", "150"])
def test_percent_value_out_of_range_raises_value_error(value):
    with pytest.raises(ValueError):
        order_total(items_for("100.00"), coupon(kind="percent", value=value), TODAY, set())


# --- fixed coupons ----------------------------------------------------------

def test_fixed_discount_applied():
    c = coupon(kind="fixed", value="20.00")
    assert order_total(items_for("120.00"), c, TODAY, set()) == Decimal("100.00")


def test_fixed_discount_capped_at_subtotal():
    c = coupon(kind="fixed", value="80.00")
    # discount capped at 50 -> 0 + shipping 10
    assert order_total(items_for("50.00"), c, TODAY, set()) == Decimal("10.00")


@pytest.mark.parametrize("value", ["0", "-1"])
def test_fixed_value_not_positive_raises_value_error(value):
    with pytest.raises(ValueError):
        order_total(items_for("100.00"), coupon(kind="fixed", value=value), TODAY, set())


# --- rounding ---------------------------------------------------------------

def test_result_rounds_half_up_to_cents():
    # 50.005 subtotal + 10 shipping = 60.005 -> 60.01
    assert order_total(items_for("50.005"), None, TODAY, set()) == Decimal("60.01")


def test_percent_discount_rounding_half_up():
    # 10.00 * 33.33% = 3.3330 -> 6.667 + 10 = 16.667 -> 16.67
    c = coupon(kind="percent", value="33.33")
    assert order_total(items_for("10.00"), c, TODAY, set()) == Decimal("16.67")


def test_result_is_two_decimal_places():
    result = order_total(items_for("120"), None, TODAY, set())
    assert result == Decimal("120.00")
    assert result.as_tuple().exponent == -2
