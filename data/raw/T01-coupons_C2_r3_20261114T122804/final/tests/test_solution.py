from datetime import date, timedelta
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 11, 14)
D = Decimal


def coupon(kind="percent", value=D(10), min_subtotal=D(0), expires=None, code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": value,
        "min_subtotal": min_subtotal,
        "expires": expires if expires is not None else TODAY + timedelta(days=30),
    }


def total(items, c=None, used=frozenset()):
    return order_total(items, c, TODAY, set(used))


# --- subtotal and shipping without coupons ---

def test_empty_order_has_no_shipping_and_zero_total():
    result = total([])
    assert result == D("0")
    assert str(result) == "0.00"


def test_small_order_pays_shipping():
    assert total([("A", D("20.00"), 1)]) == D("30.00")


def test_order_just_below_threshold_pays_shipping():
    assert total([("A", D("99.99"), 1)]) == D("109.99")


def test_order_at_threshold_ships_free():
    assert total([("A", D("100.00"), 1)]) == D("100.00")


def test_order_above_threshold_ships_free():
    assert total([("A", D("150.00"), 1)]) == D("150.00")


def test_subtotal_sums_quantities_across_items():
    items = [("A", D("10.00"), 3), ("B", D("25.50"), 2)]
    # subtotal 30 + 51 = 81, shipping 10
    assert total(items) == D("91.00")


def test_subtotal_exactly_100_from_several_items_is_free_shipping():
    items = [("A", D("40.00"), 2), ("B", D("20.00"), 1)]
    assert total(items) == D("100.00")


def test_zero_priced_item_is_allowed_and_pays_shipping():
    assert total([("FREE", D("0"), 1)]) == D("10.00")


def test_output_is_quantized_to_two_places():
    assert str(total([("A", D("100.00"), 1)])) == "100.00"
    assert str(total([("A", D("1"), 1)])) == "11.00"


# --- input validation ---

@pytest.mark.parametrize("qty", [0, -1, 1.0, "2", None, True])
def test_invalid_quantity_raises_value_error(qty):
    with pytest.raises(ValueError):
        total([("A", D("5.00"), qty)])


@pytest.mark.parametrize("price", [D("-0.01"), D("-5"), 5.0, "5.00", None])
def test_invalid_unit_price_raises_value_error(price):
    with pytest.raises(ValueError):
        total([("A", price, 1)])


def test_invalid_item_raises_even_with_coupon():
    with pytest.raises(ValueError):
        total([("A", D("5"), 0)], coupon())


# --- percent coupons ---

def test_percent_coupon_discount_and_no_shipping_when_discounted_total_ships_free():
    assert total([("A", D("200.00"), 1)], coupon("percent", D(10))) == D("180.00")


def test_percent_discount_drops_subtotal_below_threshold_adds_shipping():
    # 150 - 50% = 75, below 100 so shipping 10
    assert total([("A", D("150.00"), 1)], coupon("percent", D(50))) == D("85.00")


def test_shipping_is_computed_after_discount():
    # 120 - 20% = 96 < 100, so shipping applies even though subtotal was >= 100
    assert total([("A", D("120.00"), 1)], coupon("percent", D(20))) == D("106.00")


def test_percent_discount_landing_exactly_on_threshold_is_free_shipping():
    # 125 - 20% = 100 -> free shipping
    assert total([("A", D("125.00"), 1)], coupon("percent", D(20))) == D("100.00")


def test_percent_value_100_is_accepted_and_discounts_everything():
    # 50 - 100% = 0 -> only shipping remains
    assert total([("A", D("50.00"), 1)], coupon("percent", D(100))) == D("10.00")


@pytest.mark.parametrize("value", [D("0"), D("-5"), D("100.01"), D("250")])
def test_percent_value_out_of_range_raises_value_error(value):
    with pytest.raises(ValueError):
        total([("A", D("50.00"), 1)], coupon("percent", value))


def test_percent_value_out_of_range_is_not_coupon_error():
    with pytest.raises(ValueError) as info:
        total([("A", D("50.00"), 1)], coupon("percent", D("0")))
    assert not isinstance(info.value, CouponError)


def test_percent_rounding_is_half_up():
    # 0.05 with 50% off -> discount 0.025, remaining 0.025 + 10 shipping = 10.025 -> 10.03
    assert total([("A", D("0.05"), 1)], coupon("percent", D(50))) == D("10.03")


# --- fixed coupons ---

def test_fixed_coupon_subtracts_amount():
    # 50 - 20 = 30, shipping 10
    assert total([("A", D("50.00"), 1)], coupon("fixed", D("20"))) == D("40.00")


def test_fixed_discount_capped_at_subtotal():
    # discount capped at 50 -> 0 + shipping 10
    assert total([("A", D("50.00"), 1)], coupon("fixed", D("500"))) == D("10.00")


def test_fixed_discount_equal_to_subtotal():
    assert total([("A", D("30.00"), 1)], coupon("fixed", D("30"))) == D("10.00")


def test_fixed_shipping_computed_after_discount():
    # 110 - 15 = 95 < 100 -> shipping 10 -> 105
    assert total([("A", D("110.00"), 1)], coupon("fixed", D("15"))) == D("105.00")


def test_fixed_discount_leaving_exactly_threshold_is_free_shipping():
    # 115 - 15 = 100 -> free shipping
    assert total([("A", D("115.00"), 1)], coupon("fixed", D("15"))) == D("100.00")


@pytest.mark.parametrize("value", [D("0"), D("-1")])
def test_fixed_value_must_be_positive(value):
    with pytest.raises(ValueError):
        total([("A", D("50.00"), 1)], coupon("fixed", value))


def test_fixed_non_positive_value_is_not_coupon_error():
    with pytest.raises(ValueError) as info:
        total([("A", D("50.00"), 1)], coupon("fixed", D("0")))
    assert not isinstance(info.value, CouponError)


# --- coupon validity ---

def test_unknown_kind_raises_coupon_error():
    with pytest.raises(CouponError):
        total([("A", D("50.00"), 1)], coupon("bogus", D(10)))


def test_coupon_error_is_a_value_error():
    assert issubclass(CouponError, ValueError)


def test_coupon_valid_on_expiry_date():
    assert total([("A", D("200.00"), 1)], coupon(expires=TODAY)) == D("180.00")


def test_coupon_expired_yesterday_raises():
    with pytest.raises(CouponError):
        total([("A", D("200.00"), 1)], coupon(expires=TODAY - timedelta(days=1)))


def test_used_code_raises_coupon_error():
    with pytest.raises(CouponError):
        total([("A", D("200.00"), 1)], coupon(code="SAVE"), used={"SAVE"})


def test_other_used_codes_do_not_block_coupon():
    assert total([("A", D("200.00"), 1)], coupon(code="SAVE"), used={"OTHER"}) == D("180.00")


def test_subtotal_below_minimum_raises_coupon_error():
    with pytest.raises(CouponError):
        total([("A", D("49.99"), 1)], coupon(min_subtotal=D("50")))


def test_subtotal_equal_to_minimum_is_accepted():
    # 50 - 10% = 45 + 10 shipping
    assert total([("A", D("50.00"), 1)], coupon(min_subtotal=D("50"))) == D("55.00")


def test_minimum_is_checked_against_subtotal_not_discounted_total():
    # subtotal 60 meets minimum 60 even though discounted total is 30
    assert total([("A", D("60.00"), 1)], coupon("fixed", D("30"), min_subtotal=D("60"))) == D("40.00")


def test_empty_order_with_zero_minimum_coupon_gives_zero_total():
    assert total([], coupon("percent", D(10), min_subtotal=D("0"))) == D("0.00")


def test_empty_order_with_positive_minimum_coupon_raises():
    with pytest.raises(CouponError):
        total([], coupon(min_subtotal=D("1")))


def test_no_coupon_ignores_used_codes():
    assert total([("A", D("20.00"), 1)], None, used={"SAVE"}) == D("30.00")
