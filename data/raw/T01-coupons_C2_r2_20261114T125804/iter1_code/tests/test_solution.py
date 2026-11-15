from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 6, 15)
D = Decimal


def make_coupon(kind="percent", value=D("10"), min_subtotal=D("0"),
                expires=date(2024, 12, 31), code="SAVE"):
    return {
        "code": code,
        "kind": kind,
        "value": value,
        "min_subtotal": min_subtotal,
        "expires": expires,
    }


# --- basic totals and shipping -------------------------------------------

def test_empty_order_has_no_shipping():
    result = order_total([], None, TODAY, set())
    assert str(result) == "0.00"


def test_items_below_threshold_pay_shipping():
    result = order_total([("a", D("20.00"), 2)], None, TODAY, set())
    assert str(result) == "50.00"


def test_subtotal_exactly_100_ships_free():
    result = order_total([("a", D("50.00"), 2)], None, TODAY, set())
    assert str(result) == "100.00"


def test_subtotal_just_below_100_pays_shipping():
    result = order_total([("a", D("99.99"), 1)], None, TODAY, set())
    assert str(result) == "109.99"


def test_zero_priced_items_still_pay_shipping():
    result = order_total([("free", D("0"), 1)], None, TODAY, set())
    assert str(result) == "10.00"


def test_multiple_items_are_summed():
    items = [("a", D("10.00"), 3), ("b", D("5.50"), 2), ("c", D("1.25"), 4)]
    # subtotal = 30 + 11 + 5 = 46 -> shipping 10
    assert str(order_total(items, None, TODAY, set())) == "56.00"


def test_no_coupon_and_none_used_codes_accepted():
    assert str(order_total([("a", D("150"), 1)], None, TODAY, set())) == "150.00"


# --- percent coupons -----------------------------------------------------

def test_percent_discount_applied_and_free_shipping():
    result = order_total([("a", D("200"), 1)], make_coupon(value=D("10")), TODAY, set())
    assert str(result) == "180.00"


def test_shipping_computed_after_discount():
    # subtotal 100, 10% off -> 90, so shipping of 10 applies
    result = order_total([("a", D("100"), 1)], make_coupon(value=D("10")), TODAY, set())
    assert str(result) == "100.00"


def test_percent_100_gives_full_discount_but_shipping_still_applies():
    result = order_total([("a", D("50"), 1)], make_coupon(value=D("100")), TODAY, set())
    assert str(result) == "10.00"


def test_percent_discount_fractional_value():
    # subtotal 10.00, 15% off -> 8.50, + 10 shipping
    result = order_total([("a", D("10.00"), 1)], make_coupon(value=D("15")), TODAY, set())
    assert str(result) == "18.50"


@pytest.mark.parametrize("bad", [D("0"), D("-5"), D("100.01"), D("250")])
def test_percent_value_out_of_range_raises(bad):
    with pytest.raises(ValueError):
        order_total([("a", D("50"), 1)], make_coupon(value=bad), TODAY, set())


# --- fixed coupons -------------------------------------------------------

def test_fixed_discount_applied():
    result = order_total([("a", D("200"), 1)], make_coupon(kind="fixed", value=D("30")),
                         TODAY, set())
    assert str(result) == "170.00"


def test_fixed_discount_capped_at_subtotal():
    # subtotal 20, fixed 50 -> discount capped at 20, leaving 0 + 10 shipping
    result = order_total([("a", D("20"), 1)], make_coupon(kind="fixed", value=D("50")),
                         TODAY, set())
    assert str(result) == "10.00"


def test_fixed_discount_equal_to_subtotal():
    result = order_total([("a", D("20"), 1)], make_coupon(kind="fixed", value=D("20")),
                         TODAY, set())
    assert str(result) == "10.00"


@pytest.mark.parametrize("bad", [D("0"), D("-1")])
def test_fixed_value_must_be_positive(bad):
    with pytest.raises(ValueError):
        order_total([("a", D("50"), 1)], make_coupon(kind="fixed", value=bad), TODAY, set())


# --- coupon validity -----------------------------------------------------

def test_coupon_valid_on_expiry_day():
    coupon = make_coupon(expires=TODAY)
    assert str(order_total([("a", D("200"), 1)], coupon, TODAY, set())) == "180.00"


def test_expired_coupon_raises():
    coupon = make_coupon(expires=date(2024, 6, 14))
    with pytest.raises(CouponError):
        order_total([("a", D("200"), 1)], coupon, TODAY, set())


def test_used_coupon_raises():
    with pytest.raises(CouponError):
        order_total([("a", D("200"), 1)], make_coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_codes_do_not_block():
    result = order_total([("a", D("200"), 1)], make_coupon(code="SAVE"), TODAY,
                         {"OTHER", "ANOTHER"})
    assert str(result) == "180.00"


def test_subtotal_below_minimum_raises():
    coupon = make_coupon(min_subtotal=D("50.01"))
    with pytest.raises(CouponError):
        order_total([("a", D("50"), 1)], coupon, TODAY, set())


def test_subtotal_equal_to_minimum_accepted():
    coupon = make_coupon(min_subtotal=D("50"), value=D("10"))
    # 50 - 5 = 45, + 10 shipping
    assert str(order_total([("a", D("50"), 1)], coupon, TODAY, set())) == "55.00"


def test_unknown_coupon_kind_raises():
    with pytest.raises(CouponError):
        order_total([("a", D("50"), 1)], make_coupon(kind="bogus"), TODAY, set())


def test_coupon_error_is_value_error():
    assert issubclass(CouponError, ValueError)


# --- item validation -----------------------------------------------------

@pytest.mark.parametrize("qty", [0, -1, 1.5, "2", None])
def test_invalid_quantity_raises(qty):
    with pytest.raises(ValueError):
        order_total([("a", D("10"), qty)], None, TODAY, set())


def test_boolean_quantity_raises():
    with pytest.raises(ValueError):
        order_total([("a", D("10"), True)], None, TODAY, set())


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        order_total([("a", D("-0.01"), 1)], None, TODAY, set())


def test_zero_unit_price_allowed():
    assert str(order_total([("a", D("0"), 1)], None, TODAY, set())) == "10.00"


# --- rounding ------------------------------------------------------------

def test_half_cent_rounds_up():
    # subtotal 10.005 + 10 shipping = 20.005 -> 20.01 with ROUND_HALF_UP
    assert str(order_total([("a", D("10.005"), 1)], None, TODAY, set())) == "20.01"


def test_result_always_has_two_decimals():
    result = order_total([("a", D("3"), 1)], None, TODAY, set())
    assert result == D("13.00")
    assert str(result) == "13.00"
