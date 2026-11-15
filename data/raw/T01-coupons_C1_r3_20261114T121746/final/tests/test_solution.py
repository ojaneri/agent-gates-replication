from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 15)
FUTURE = date(2027, 1, 1)
PAST = date(2026, 1, 1)


def coupon(kind="percent", value=Decimal("10"), min_subtotal=Decimal("0"),
           expires=FUTURE, code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": value,
        "min_subtotal": min_subtotal,
        "expires": expires,
    }


def item(price="20.00", qty=1, sku="A"):
    return (sku, Decimal(price), qty)


# --- subtotal and shipping without coupons ---

def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == Decimal("0.00")


def test_small_order_pays_shipping():
    assert order_total([item("20.00")], None, TODAY, set()) == Decimal("30.00")


def test_order_below_threshold_pays_shipping():
    assert order_total([item("99.99")], None, TODAY, set()) == Decimal("109.99")


def test_order_at_threshold_is_free_shipping():
    assert order_total([item("100.00")], None, TODAY, set()) == Decimal("100.00")


def test_subtotal_sums_multiple_lines_and_quantities():
    items = [item("10.00", 2, "A"), item("5.50", 3, "B")]
    # subtotal 36.50 -> shipping 10.00
    assert order_total(items, None, TODAY, set()) == Decimal("46.50")


def test_zero_priced_items_still_pay_shipping():
    assert order_total([item("0.00")], None, TODAY, set()) == Decimal("10.00")


# --- input validation ---

@pytest.mark.parametrize("qty", [0, -1])
def test_quantity_below_one_rejected(qty):
    with pytest.raises(ValueError):
        order_total([item("5.00", qty)], None, TODAY, set())


def test_quantity_must_be_int():
    with pytest.raises(ValueError):
        order_total([("A", Decimal("5.00"), 1.5)], None, TODAY, set())


def test_quantity_bool_rejected():
    with pytest.raises(ValueError):
        order_total([("A", Decimal("5.00"), True)], None, TODAY, set())


def test_negative_unit_price_rejected():
    with pytest.raises(ValueError):
        order_total([item("-0.01")], None, TODAY, set())


# --- coupon validity ---

def test_expired_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([item("50.00")], coupon(expires=PAST), TODAY, set())


def test_coupon_valid_on_expiry_date():
    c = coupon(expires=TODAY)
    # subtotal 50 -> 10% off = 45 -> shipping 10 -> 55
    assert order_total([item("50.00")], c, TODAY, set()) == Decimal("55.00")


def test_used_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([item("50.00")], coupon(code="ONCE"), TODAY, {"ONCE"})


def test_other_used_codes_do_not_block():
    assert order_total([item("50.00")], coupon(code="NEW"), TODAY, {"OLD"}) == Decimal("55.00")


def test_subtotal_below_minimum_rejected():
    with pytest.raises(CouponError):
        order_total([item("49.99")], coupon(min_subtotal=Decimal("50")), TODAY, set())


def test_subtotal_equal_to_minimum_accepted():
    c = coupon(min_subtotal=Decimal("50"))
    assert order_total([item("50.00")], c, TODAY, set()) == Decimal("55.00")


def test_unknown_kind_rejected():
    with pytest.raises(CouponError):
        order_total([item("50.00")], coupon(kind="bogus"), TODAY, set())


def test_empty_order_with_minimum_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([], coupon(min_subtotal=Decimal("1")), TODAY, set())


def test_empty_order_with_zero_minimum_coupon_has_no_shipping():
    assert order_total([], coupon(kind="fixed", value=Decimal("5")), TODAY, set()) == Decimal("0.00")


# --- percent coupons ---

def test_percent_discount_applied_before_shipping():
    # 80.00 -> 25% off = 60.00 -> shipping 10.00
    c = coupon(value=Decimal("25"))
    assert order_total([item("80.00")], c, TODAY, set()) == Decimal("70.00")


def test_percent_discount_can_make_order_free_shipping():
    # 120.00 -> 20% off = 96.00 -> below 100 -> shipping 10.00
    assert order_total([item("120.00")], coupon(value=Decimal("20")), TODAY, set()) == Decimal("106.00")
    # 110.00 -> 5% off = 104.50 -> free shipping
    assert order_total([item("110.00")], coupon(value=Decimal("5")), TODAY, set()) == Decimal("104.50")


def test_percent_100_gives_zero_plus_shipping():
    assert order_total([item("40.00")], coupon(value=Decimal("100")), TODAY, set()) == Decimal("10.00")


@pytest.mark.parametrize("value", [Decimal("0"), Decimal("-5"), Decimal("100.01")])
def test_percent_value_out_of_range_rejected(value):
    with pytest.raises(ValueError):
        order_total([item("50.00")], coupon(value=value), TODAY, set())


def test_percent_rounding_half_up():
    # 10.05 * 0.5 = 5.025 discount; subtotal stays 10.05 -> 5.025 off -> 5.025 + 10 shipping
    # discounted = 10.05 - 5.025 = 5.025; total = 15.025 -> 15.03 (half up)
    c = coupon(value=Decimal("50"))
    assert order_total([item("10.05")], c, TODAY, set()) == Decimal("15.03")


# --- fixed coupons ---

def test_fixed_discount_applied():
    c = coupon(kind="fixed", value=Decimal("15.00"))
    # 60 - 15 = 45 -> shipping 10 -> 55
    assert order_total([item("60.00")], c, TODAY, set()) == Decimal("55.00")


def test_fixed_discount_capped_at_subtotal():
    c = coupon(kind="fixed", value=Decimal("500"))
    # discount capped to 20 -> 0 -> shipping 10
    assert order_total([item("20.00")], c, TODAY, set()) == Decimal("10.00")


@pytest.mark.parametrize("value", [Decimal("0"), Decimal("-1")])
def test_fixed_value_must_be_positive(value):
    with pytest.raises(ValueError):
        order_total([item("50.00")], coupon(kind="fixed", value=value), TODAY, set())


def test_fixed_discount_can_bring_order_under_threshold():
    c = coupon(kind="fixed", value=Decimal("30"))
    # 120 - 30 = 90 -> shipping 10 -> 100
    assert order_total([item("120.00")], c, TODAY, set()) == Decimal("100.00")


def test_fixed_discount_with_exact_threshold_after_discount_is_free():
    c = coupon(kind="fixed", value=Decimal("20"))
    # 120 - 20 = 100 -> free shipping
    assert order_total([item("120.00")], c, TODAY, set()) == Decimal("100.00")


def test_order_none_coupon_equivalent_to_no_discount():
    assert order_total([item("30.00")], None, TODAY, set()) == order_total(
        [item("30.00")], None, TODAY, {"X"})
