from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 6, 15)


def coupon(kind="percent", value="10", min_subtotal="0", expires=date(2024, 12, 31), code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": Decimal(value),
        "min_subtotal": Decimal(min_subtotal),
        "expires": expires,
    }


def item(price, qty=1, sku="A"):
    return (sku, Decimal(price), qty)


# --- subtotal and shipping without coupons ---

def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == Decimal("0.00")


def test_small_order_pays_shipping():
    assert order_total([item("20.00", 2)], None, TODAY, set()) == Decimal("50.00")


def test_order_below_100_pays_shipping():
    assert order_total([item("99.99")], None, TODAY, set()) == Decimal("109.99")


def test_order_exactly_100_is_free_shipping():
    assert order_total([item("100.00")], None, TODAY, set()) == Decimal("100.00")


def test_subtotal_sums_multiple_items():
    items = [item("10.50", 2, "A"), item("3.25", 4, "B")]
    # 21.00 + 13.00 = 34.00 -> +10 shipping
    assert order_total(items, None, TODAY, set()) == Decimal("44.00")


def test_zero_price_item_still_pays_shipping():
    assert order_total([item("0.00")], None, TODAY, set()) == Decimal("10.00")


# --- input validation ---

@pytest.mark.parametrize("qty", [0, -1])
def test_quantity_below_one_rejected(qty):
    with pytest.raises(ValueError):
        order_total([item("5.00", qty)], None, TODAY, set())


def test_non_integer_quantity_rejected():
    with pytest.raises(ValueError):
        order_total([("A", Decimal("5.00"), 1.5)], None, TODAY, set())


def test_negative_price_rejected():
    with pytest.raises(ValueError):
        order_total([item("-0.01")], None, TODAY, set())


def test_zero_price_accepted():
    assert order_total([item("0")], None, TODAY, set()) == Decimal("10.00")


# --- coupon validity ---

def test_expired_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([item("200.00")], coupon(expires=date(2024, 6, 14)), TODAY, set())


def test_coupon_valid_on_expiry_date():
    c = coupon(expires=TODAY)
    assert order_total([item("200.00")], c, TODAY, set()) == Decimal("180.00")


def test_used_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([item("200.00")], coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_code_does_not_block():
    assert order_total([item("200.00")], coupon(code="SAVE"), TODAY, {"OTHER"}) == Decimal("180.00")


def test_below_min_subtotal_rejected():
    with pytest.raises(CouponError):
        order_total([item("49.99")], coupon(min_subtotal="50.00"), TODAY, set())


def test_min_subtotal_equal_accepted():
    c = coupon(kind="fixed", value="5", min_subtotal="50.00")
    # 50 - 5 = 45 -> shipping 10 -> 55
    assert order_total([item("50.00")], c, TODAY, set()) == Decimal("55.00")


def test_unknown_coupon_kind_rejected():
    with pytest.raises(CouponError):
        order_total([item("200.00")], coupon(kind="bogus"), TODAY, set())


# --- percent coupons ---

def test_percent_discount():
    # 200 - 20 = 180, free shipping
    assert order_total([item("200.00")], coupon(value="10"), TODAY, set()) == Decimal("180.00")


def test_percent_discount_can_drop_below_100_and_add_shipping():
    # 120 - 30 = 90 -> shipping 10 -> 100
    assert order_total([item("120.00")], coupon(value="25"), TODAY, set()) == Decimal("100.00")


def test_percent_100_gives_free_order_plus_shipping():
    # 0 after discount -> shipping 10
    assert order_total([item("50.00")], coupon(value="100"), TODAY, set()) == Decimal("10.00")


@pytest.mark.parametrize("value", ["0", "-5", "100.01", "150"])
def test_percent_value_out_of_range_rejected(value):
    with pytest.raises(ValueError):
        order_total([item("200.00")], coupon(value=value), TODAY, set())


def test_percent_rounding_half_up():
    # 10.05 * 10% ... use subtotal 100.05 -> discount 10.005 -> after 90.045 -> +10 = 100.045 -> 100.05
    result = order_total([item("100.05")], coupon(value="10"), TODAY, set())
    assert result == Decimal("100.05")


# --- fixed coupons ---

def test_fixed_discount():
    # 150 - 20 = 130, free shipping
    assert order_total([item("150.00")], coupon(kind="fixed", value="20"), TODAY, set()) == Decimal("130.00")


def test_fixed_discount_capped_at_subtotal():
    # subtotal 30 - min(50, 30) = 0 -> shipping 10
    c = coupon(kind="fixed", value="50")
    assert order_total([item("30.00")], c, TODAY, set()) == Decimal("10.00")


@pytest.mark.parametrize("value", ["0", "-1"])
def test_fixed_value_not_positive_rejected(value):
    with pytest.raises(ValueError):
        order_total([item("200.00")], coupon(kind="fixed", value=value), TODAY, set())


def test_fixed_discount_can_push_order_under_threshold():
    # 110 - 20 = 90 -> shipping 10 -> 100
    assert order_total([item("110.00")], coupon(kind="fixed", value="20"), TODAY, set()) == Decimal("100.00")


# --- rounding ---

def test_result_rounded_half_up_to_cents():
    # subtotal 100.00 with 3.333...% style value: 100 * 0.5 / 100... use fixed-like check
    # percent 0.005 of 100.00 is 0.005; total 99.995 + 10 shipping = 109.995 -> 110.00
    c = coupon(value="0.005")
    assert order_total([item("99.99"), item("0.01", 1, "B")], c, TODAY, set()) == Decimal("110.00")


def test_result_has_two_decimal_places():
    result = order_total([item("1.5")], None, TODAY, set())
    assert result == Decimal("11.50")
    assert result.as_tuple().exponent == -2
