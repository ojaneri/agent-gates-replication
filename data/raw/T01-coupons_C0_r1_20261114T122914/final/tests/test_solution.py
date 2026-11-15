from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 15)


def coupon(kind="percent", value="10", min_subtotal="0", expires=date(2026, 12, 31),
           code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": Decimal(value),
        "min_subtotal": Decimal(min_subtotal),
        "expires": expires,
    }


def D(s):
    return Decimal(s)


# Subtotal and shipping without coupons

def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_small_order_pays_shipping():
    items = [("A", D("20.00"), 2)]  # 40.00
    assert order_total(items, None, TODAY, set()) == D("50.00")


def test_order_at_100_ships_free():
    items = [("A", D("50.00"), 2)]  # 100.00
    assert order_total(items, None, TODAY, set()) == D("100.00")


def test_order_just_below_100_pays_shipping():
    items = [("A", D("99.99"), 1)]
    assert order_total(items, None, TODAY, set()) == D("109.99")


def test_subtotal_sums_multiple_items():
    items = [("A", D("30.00"), 2), ("B", D("12.50"), 4)]  # 60 + 50 = 110
    assert order_total(items, None, TODAY, set()) == D("110.00")


def test_zero_price_item_still_pays_shipping():
    items = [("FREE", D("0"), 1)]
    assert order_total(items, None, TODAY, set()) == D("10.00")


# Percent coupons

def test_percent_coupon_applied_then_shipping_computed():
    # 120 - 10% = 108 -> free shipping
    items = [("A", D("120.00"), 1)]
    assert order_total(items, coupon(value="10"), TODAY, set()) == D("108.00")


def test_percent_discount_drops_below_100_adds_shipping():
    # 105 - 10% = 94.5 -> shipping 10 -> 104.5
    items = [("A", D("105.00"), 1)]
    assert order_total(items, coupon(value="10"), TODAY, set()) == D("104.50")


def test_percent_100_gives_only_shipping_on_zero_subtotal_order():
    items = [("A", D("50.00"), 1)]
    # discount 50, after discount 0 -> items present, so shipping 10
    assert order_total(items, coupon(value="100"), TODAY, set()) == D("10.00")


def test_percent_rounds_half_up():
    # 10.05 * 1 with 25% off -> discount 2.5125 -> after 7.5375 + 10 = 17.5375 -> 17.54
    items = [("A", D("10.05"), 1)]
    assert order_total(items, coupon(value="25"), TODAY, set()) == D("17.54")


def test_percent_zero_is_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("50"), 1)], coupon(value="0"), TODAY, set())


def test_percent_over_100_is_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("50"), 1)], coupon(value="100.01"), TODAY, set())


def test_percent_negative_is_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("50"), 1)], coupon(value="-5"), TODAY, set())


# Fixed coupons

def test_fixed_coupon_subtracts_amount():
    items = [("A", D("120.00"), 1)]
    assert order_total(items, coupon(kind="fixed", value="20"), TODAY, set()) == D("100.00")


def test_fixed_discount_capped_at_subtotal():
    items = [("A", D("5.00"), 1)]
    # discount capped to 5 -> after discount 0 -> shipping 10
    assert order_total(items, coupon(kind="fixed", value="50"), TODAY, set()) == D("10.00")


def test_fixed_zero_is_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("50"), 1)], coupon(kind="fixed", value="0"), TODAY, set())


def test_fixed_negative_is_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("50"), 1)], coupon(kind="fixed", value="-1"), TODAY, set())


# Coupon validity

def test_expired_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([("A", D("50"), 1)],
                    coupon(expires=date(2026, 6, 14)), TODAY, set())


def test_coupon_valid_on_expiry_day():
    items = [("A", D("50"), 1)]
    # 10% off 50 = 45 -> shipping 10 -> 55
    assert order_total(items, coupon(expires=TODAY), TODAY, set()) == D("55.00")


def test_used_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([("A", D("50"), 1)], coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_codes_do_not_block():
    items = [("A", D("50"), 1)]
    assert order_total(items, coupon(code="SAVE"), TODAY, {"OTHER"}) == D("55.00")


def test_subtotal_below_minimum_rejected():
    with pytest.raises(CouponError):
        order_total([("A", D("49.99"), 1)], coupon(min_subtotal="50"), TODAY, set())


def test_subtotal_equal_to_minimum_accepted():
    items = [("A", D("50"), 1)]
    assert order_total(items, coupon(min_subtotal="50"), TODAY, set()) == D("55.00")


def test_unknown_coupon_kind_rejected():
    with pytest.raises(CouponError):
        order_total([("A", D("50"), 1)], coupon(kind="bogus"), TODAY, set())


# Item validation

def test_quantity_zero_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("10"), 0)], None, TODAY, set())


def test_negative_quantity_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("10"), -1)], None, TODAY, set())


def test_negative_unit_price_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("-1"), 1)], None, TODAY, set())


def test_zero_unit_price_accepted():
    assert order_total([("A", D("0"), 1)], None, TODAY, set()) == D("10.00")
