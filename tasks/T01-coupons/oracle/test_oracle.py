from datetime import date
from decimal import Decimal as D

import pytest

from solution import order_total, CouponError

TODAY = date(2026, 11, 14)


def coupon(**kw):
    c = {"code": "SAVE10", "kind": "percent", "value": D("10"), "min_subtotal": D("0"),
         "expires": date(2026, 12, 31)}
    c.update(kw)
    return c


# subtotal and shipping
def test_simple_order_with_shipping():
    assert order_total([("a", D("20.00"), 2)], None, TODAY, set()) == D("50.00")


def test_free_shipping_at_exactly_100():
    assert order_total([("a", D("50.00"), 2)], None, TODAY, set()) == D("100.00")


def test_shipping_just_below_100():
    assert order_total([("a", D("99.99"), 1)], None, TODAY, set()) == D("109.99")


def test_empty_order_is_zero():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_multiple_items():
    items = [("a", D("10.00"), 3), ("b", D("5.50"), 2), ("c", D("0"), 4)]
    assert order_total(items, None, TODAY, set()) == D("51.00")


# validation
@pytest.mark.parametrize("qty", [0, -1, 1.5, True])
def test_invalid_quantity(qty):
    with pytest.raises(ValueError):
        order_total([("a", D("10"), qty)], None, TODAY, set())


def test_negative_price():
    with pytest.raises(ValueError):
        order_total([("a", D("-0.01"), 1)], None, TODAY, set())


# percent coupons
def test_percent_coupon_and_free_shipping():
    assert order_total([("a", D("200.00"), 1)], coupon(), TODAY, set()) == D("180.00")


def test_shipping_uses_discounted_subtotal():
    # 105 - 10% = 94.50 -> below 100, shipping applies
    assert order_total([("a", D("105.00"), 1)], coupon(), TODAY, set()) == D("104.50")


def test_percent_100_is_allowed():
    assert order_total([("a", D("40.00"), 1)], coupon(value=D("100")), TODAY, set()) == D("10.00")


def test_fractional_percent_is_valid():
    # 0.5% of 200.00 = 1.00 -> 199.00, free shipping
    assert order_total([("a", D("200.00"), 1)], coupon(value=D("0.5")), TODAY, set()) == D("199.00")


def test_fractional_fixed_is_valid():
    assert order_total([("a", D("200.00"), 1)], coupon(kind="fixed", value=D("0.50")), TODAY, set()) == D("199.50")


@pytest.mark.parametrize("value", [D("0"), D("-5"), D("100.01")])
def test_invalid_percent(value):
    with pytest.raises(ValueError):
        order_total([("a", D("40.00"), 1)], coupon(value=value), TODAY, set())


def test_rounding_half_up():
    # 1.25 with 50% off = 0.625, plus 10.00 shipping = 10.625 -> 10.63
    assert order_total([("a", D("1.25"), 1)], coupon(value=D("50")), TODAY, set()) == D("10.63")


def test_rounding_half_up_not_bankers():
    # 0.25 * 50% = 0.125 -> 0.13 with ROUND_HALF_UP (banker's would give 0.12)
    assert order_total([("a", D("0.25"), 1)], coupon(value=D("50")), TODAY, set()) == D("10.13")


# fixed coupons
def test_fixed_coupon():
    assert order_total([("a", D("130.00"), 1)], coupon(kind="fixed", value=D("20")), TODAY, set()) == D("110.00")


def test_fixed_coupon_capped_at_subtotal():
    assert order_total([("a", D("15.00"), 1)], coupon(kind="fixed", value=D("50")), TODAY, set()) == D("10.00")


def test_fixed_coupon_must_be_positive():
    with pytest.raises(ValueError):
        order_total([("a", D("15.00"), 1)], coupon(kind="fixed", value=D("0")), TODAY, set())


# coupon validity
def test_coupon_valid_on_expiry_day():
    assert order_total([("a", D("200.00"), 1)], coupon(expires=TODAY), TODAY, set()) == D("180.00")


def test_coupon_expired_day_after():
    with pytest.raises(CouponError):
        order_total([("a", D("200.00"), 1)], coupon(expires=date(2026, 11, 13)), TODAY, set())


def test_used_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([("a", D("200.00"), 1)], coupon(), TODAY, {"SAVE10"})


def test_other_used_codes_do_not_matter():
    assert order_total([("a", D("200.00"), 1)], coupon(), TODAY, {"OTHER"}) == D("180.00")


def test_min_subtotal_equal_is_accepted():
    assert order_total([("a", D("50.00"), 1)], coupon(min_subtotal=D("50.00")), TODAY, set()) == D("55.00")


def test_min_subtotal_below_rejected():
    with pytest.raises(CouponError):
        order_total([("a", D("49.99"), 1)], coupon(min_subtotal=D("50.00")), TODAY, set())


def test_unknown_kind():
    with pytest.raises(CouponError):
        order_total([("a", D("50.00"), 1)], coupon(kind="bogo"), TODAY, set())


def test_coupon_error_is_value_error():
    assert issubclass(CouponError, ValueError)


def test_result_is_decimal_with_two_places():
    r = order_total([("a", D("3.333"), 3)], None, TODAY, set())
    assert isinstance(r, D) and r == D("20.00") and r.as_tuple().exponent == -2
