from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 15)
D = Decimal


def coupon(kind="percent", value=D("10"), min_subtotal=D("0"),
           expires=date(2026, 12, 31), code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": value,
        "min_subtotal": min_subtotal,
        "expires": expires,
    }


def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_empty_order_with_coupon_is_zero():
    assert order_total([], coupon("fixed", D("5")), TODAY, set()) == D("0.00")


def test_no_coupon_below_threshold_pays_shipping():
    items = [("A", D("20.00"), 2)]
    assert order_total(items, None, TODAY, set()) == D("50.00")


def test_no_coupon_at_threshold_ships_free():
    items = [("A", D("50.00"), 2)]
    assert order_total(items, None, TODAY, set()) == D("100.00")


def test_subtotal_sums_quantities():
    items = [("A", D("1.50"), 3), ("B", D("2.25"), 4)]
    # subtotal 4.50 + 9.00 = 13.50, shipping 10.00
    assert order_total(items, None, TODAY, set()) == D("23.50")


def test_percent_discount_applied_before_shipping_threshold():
    # 110 subtotal, 10% off -> 99 < 100, so shipping applies
    items = [("A", D("110.00"), 1)]
    assert order_total(items, coupon("percent", D("10")), TODAY, set()) == D("109.00")


def test_percent_discount_drops_below_threshold_into_shipping():
    items = [("A", D("100.00"), 1)]
    # 100 - 1 = 99 -> shipping 10 -> 109
    assert order_total(items, coupon("percent", D("1")), TODAY, set()) == D("109.00")


def test_percent_discount_keeps_free_shipping():
    items = [("A", D("200.00"), 1)]
    # 200 - 20 = 180 -> free shipping
    assert order_total(items, coupon("percent", D("10")), TODAY, set()) == D("180.00")


def test_percent_100_gives_zero_plus_shipping_rules():
    items = [("A", D("30.00"), 1)]
    # discount 30 -> discounted 0 -> below threshold -> shipping 10
    assert order_total(items, coupon("percent", D("100")), TODAY, set()) == D("10.00")


def test_fixed_discount_applied():
    items = [("A", D("120.00"), 1)]
    assert order_total(items, coupon("fixed", D("20")), TODAY, set()) == D("100.00")


def test_fixed_discount_capped_at_subtotal():
    items = [("A", D("30.00"), 1)]
    # discount capped at 30 -> discounted 0 -> shipping 10
    assert order_total(items, coupon("fixed", D("500"), min_subtotal=D("0")),
                       TODAY, set()) == D("10.00")


def test_rounding_half_up():
    # subtotal 100.05 with 0% rounding: use percent 1 -> discount 1.0005
    # discounted 99.0495 -> shipping 10 -> 109.0495 -> 109.05
    items = [("A", D("100.05"), 1)]
    assert order_total(items, coupon("percent", D("1")), TODAY, set()) == D("109.05")


def test_rounding_half_up_exact_half():
    # 0.125 -> 0.13 with ROUND_HALF_UP; subtotal 100.00 free shipping
    items = [("A", D("100.00"), 1)]
    # percent 0.125 -> discount 0.125 -> 99.875 -> shipping 10 -> 109.875 -> 109.88
    assert order_total(items, coupon("percent", D("0.125")), TODAY, set()) == D("109.88")


def test_expiry_day_is_still_valid():
    items = [("A", D("100.00"), 1)]
    c = coupon("fixed", D("10"), expires=TODAY)
    # 100 - 10 = 90 -> below threshold -> shipping 10
    assert order_total(items, c, TODAY, set()) == D("100.00")


def test_expired_coupon_raises():
    items = [("A", D("100.00"), 1)]
    c = coupon("fixed", D("10"), expires=date(2026, 6, 14))
    with pytest.raises(CouponError):
        order_total(items, c, TODAY, set())


def test_used_code_raises():
    items = [("A", D("100.00"), 1)]
    with pytest.raises(CouponError):
        order_total(items, coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_code_does_not_block():
    items = [("A", D("100.00"), 1)]
    # 100 - 10 = 90 -> shipping 10
    assert order_total(items, coupon("fixed", D("10"), code="NEW"),
                       TODAY, {"OLD"}) == D("100.00")


def test_min_subtotal_equal_is_accepted():
    items = [("A", D("50.00"), 2)]
    c = coupon("fixed", D("5"), min_subtotal=D("100.00"))
    # subtotal 100 accepted; 100 - 5 = 95 -> shipping 10 -> 105
    assert order_total(items, c, TODAY, set()) == D("105.00")


def test_below_min_subtotal_raises():
    items = [("A", D("49.99"), 2)]
    c = coupon("fixed", D("5"), min_subtotal=D("100.00"))
    with pytest.raises(CouponError):
        order_total(items, c, TODAY, set())


def test_unknown_kind_raises_coupon_error():
    items = [("A", D("100.00"), 1)]
    with pytest.raises(CouponError):
        order_total(items, coupon("bogus", D("5")), TODAY, set())


@pytest.mark.parametrize("value", [D("0"), D("-1"), D("100.01")])
def test_percent_value_out_of_range_raises(value):
    items = [("A", D("100.00"), 1)]
    with pytest.raises(ValueError):
        order_total(items, coupon("percent", value), TODAY, set())


@pytest.mark.parametrize("value", [D("0"), D("-5")])
def test_fixed_value_must_be_positive(value):
    items = [("A", D("100.00"), 1)]
    with pytest.raises(ValueError):
        order_total(items, coupon("fixed", value), TODAY, set())


def test_percent_100_is_allowed():
    items = [("A", D("100.00"), 1)]
    # discount whole subtotal -> 0 -> shipping 10
    assert order_total(items, coupon("percent", D("100")), TODAY, set()) == D("10.00")


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_below_one_raises(quantity):
    with pytest.raises(ValueError):
        order_total([("A", D("1.00"), quantity)], None, TODAY, set())


def test_quantity_must_be_int():
    with pytest.raises(ValueError):
        order_total([("A", D("1.00"), 1.5)], None, TODAY, set())


def test_quantity_bool_rejected():
    with pytest.raises(ValueError):
        order_total([("A", D("1.00"), True)], None, TODAY, set())


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        order_total([("A", D("-0.01"), 1)], None, TODAY, set())


def test_zero_unit_price_allowed():
    # free item, subtotal 0 but items present -> shipping applies
    assert order_total([("A", D("0"), 1)], None, TODAY, set()) == D("10.00")


def test_invalid_item_checked_before_coupon():
    with pytest.raises(ValueError):
        order_total([("A", D("1.00"), 0)], coupon("bogus"), TODAY, {"SAVE"})
