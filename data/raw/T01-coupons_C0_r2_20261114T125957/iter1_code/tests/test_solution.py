from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 1)


def coupon(kind="percent", value="10", min_subtotal="0", expires=date(2026, 12, 31), code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": Decimal(value),
        "min_subtotal": Decimal(min_subtotal),
        "expires": expires,
    }


def item(price, qty=1, sku="sku"):
    return (sku, Decimal(price), qty)


# --- subtotal and shipping ---

def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == Decimal("0.00")


def test_below_threshold_pays_shipping():
    assert order_total([item("5.00", 2)], None, TODAY, set()) == Decimal("20.00")


def test_99_99_still_pays_shipping():
    assert order_total([item("99.99")], None, TODAY, set()) == Decimal("109.99")


def test_exactly_100_ships_free():
    assert order_total([item("100.00")], None, TODAY, set()) == Decimal("100.00")


def test_subtotal_is_sum_of_price_times_quantity():
    items = [item("12.50", 3, "a"), item("0.25", 4, "b")]
    # subtotal 37.50 + 1.00 = 38.50 -> shipping 10 -> 48.50
    assert order_total(items, None, TODAY, set()) == Decimal("48.50")


def test_zero_priced_items_still_pay_shipping():
    assert order_total([item("0.00")], None, TODAY, set()) == Decimal("10.00")


# --- percent coupons ---

def test_percent_discount():
    # subtotal 120, 10% off = 108, free shipping
    assert order_total([item("60.00", 2)], coupon("percent", "10"), TODAY, set()) == Decimal("108.00")


def test_percent_discount_brings_subtotal_below_threshold_adds_shipping():
    # subtotal 110, 20% off = 88, shipping 10 -> 98
    assert order_total([item("110.00")], coupon("percent", "20"), TODAY, set()) == Decimal("98.00")


def test_percent_100_gives_zero_plus_shipping():
    assert order_total([item("50.00")], coupon("percent", "100"), TODAY, set()) == Decimal("10.00")


def test_percent_zero_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("50.00")], coupon("percent", "0"), TODAY, set())


def test_percent_over_100_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("50.00")], coupon("percent", "101"), TODAY, set())


def test_percent_negative_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("50.00")], coupon("percent", "-5"), TODAY, set())


# --- fixed coupons ---

def test_fixed_discount():
    # 50 - 15 = 35, shipping 10 -> 45
    assert order_total([item("50.00")], coupon("fixed", "15"), TODAY, set()) == Decimal("45.00")


def test_fixed_discount_capped_at_subtotal():
    # subtotal 5, discount capped at 5 -> 0, shipping 10 -> 10
    assert order_total([item("5.00")], coupon("fixed", "20"), TODAY, set()) == Decimal("10.00")


def test_fixed_discount_can_make_order_free_shipping():
    # 150 - 60 = 90 -> shipping 10 -> 100 (not free: 90 < 100)
    assert order_total([item("150.00")], coupon("fixed", "60"), TODAY, set()) == Decimal("100.00")
    # 150 - 40 = 110 -> free shipping -> 110
    assert order_total([item("150.00")], coupon("fixed", "40"), TODAY, set()) == Decimal("110.00")


def test_fixed_zero_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("50.00")], coupon("fixed", "0"), TODAY, set())


def test_fixed_negative_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("50.00")], coupon("fixed", "-1"), TODAY, set())


# --- coupon validity ---

def test_coupon_valid_on_expiry_date():
    c = coupon("fixed", "5", expires=TODAY)
    assert order_total([item("50.00")], c, TODAY, set()) == Decimal("55.00")


def test_expired_coupon_is_rejected():
    c = coupon(expires=date(2026, 5, 31))
    with pytest.raises(CouponError):
        order_total([item("50.00")], c, TODAY, set())


def test_used_coupon_is_rejected():
    with pytest.raises(CouponError):
        order_total([item("50.00")], coupon(code="ONCE"), TODAY, {"ONCE"})


def test_other_used_codes_do_not_block():
    assert order_total([item("50.00")], coupon(code="NEW"), TODAY, {"OLD"}) == Decimal("55.00")


def test_subtotal_equal_to_minimum_is_accepted():
    c = coupon("fixed", "5", min_subtotal="50.00")
    assert order_total([item("50.00")], c, TODAY, set()) == Decimal("55.00")


def test_subtotal_below_minimum_is_rejected():
    c = coupon("fixed", "5", min_subtotal="50.00")
    with pytest.raises(CouponError):
        order_total([item("49.99")], c, TODAY, set())


def test_unknown_kind_is_rejected():
    with pytest.raises(CouponError):
        order_total([item("50.00")], coupon("bogus", "5"), TODAY, set())


# --- item validation ---

def test_zero_quantity_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("5.00", 0)], None, TODAY, set())


def test_negative_quantity_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("5.00", -1)], None, TODAY, set())


def test_float_quantity_is_rejected():
    with pytest.raises(ValueError):
        order_total([("sku", Decimal("5.00"), 1.5)], None, TODAY, set())


def test_negative_unit_price_is_rejected():
    with pytest.raises(ValueError):
        order_total([item("-0.01")], None, TODAY, set())


# --- rounding ---

def test_result_rounded_half_up():
    # 10.10 with 5% off = 9.595; + 10 shipping = 19.595 -> 19.60
    assert order_total([item("10.10")], coupon("percent", "5"), TODAY, set()) == Decimal("19.60")


def test_result_has_two_decimal_places():
    # 10.00 with 33.33% off = 6.667 + 10 = 16.667 -> 16.67
    assert order_total([item("10.00")], coupon("percent", "33.33"), TODAY, set()) == Decimal("16.67")
