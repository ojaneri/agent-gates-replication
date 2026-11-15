from datetime import date, timedelta
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 11, 14)


def make_coupon(**overrides):
    base = {
        "code": "SAVE",
        "kind": "percent",
        "value": D("10"),
        "min_subtotal": D("0"),
        "expires": date(2026, 12, 31),
    }
    base.update(overrides)
    return base


def item(price="10.00", qty=1, sku="sku"):
    return (sku, D(price), qty)


def total(items, coupon=None, used=frozenset()):
    return order_total(items, coupon, TODAY, set(used))


# --- basic totals and shipping ---

def test_empty_order_is_zero_with_no_shipping():
    assert total([]) == D("0.00")


def test_empty_order_with_fixed_coupon_is_zero():
    assert total([], make_coupon(kind="fixed", value=D("5"))) == D("0.00")


def test_shipping_charged_below_threshold():
    assert total([item("10.00")]) == D("20.00")


def test_free_shipping_at_threshold():
    assert total([item("100.00")]) == D("100.00")


def test_shipping_charged_just_below_threshold():
    assert total([item("99.99")]) == D("109.99")


def test_free_shipping_just_above_threshold():
    assert total([item("100.01")]) == D("100.01")


def test_subtotal_sums_all_lines():
    items = [item("2.50", 3, "a"), item("1.00", 2, "b")]
    assert total(items) == D("19.50")


def test_zero_price_item_still_pays_shipping():
    assert total([item("0.00")]) == D("10.00")


def test_quantity_one_is_accepted():
    assert total([item("100.00", 1)]) == D("100.00")


# --- percent coupons ---

def test_percent_discount_applied():
    assert total([item("200.00")], make_coupon(value=D("10"))) == D("180.00")


def test_shipping_uses_discounted_subtotal():
    # 105.00 minus 10% is 94.50, which is below 100, so shipping applies.
    assert total([item("105.00")], make_coupon(value=D("10"))) == D("104.50")


def test_percent_100_gives_free_goods_plus_shipping():
    assert total([item("50.00")], make_coupon(value=D("100"))) == D("10.00")


def test_percent_small_value_accepted():
    # 100.00 minus 0.5% is 99.50, below the free-shipping threshold: 99.50 + 10.00
    assert total([item("100.00")], make_coupon(value=D("0.5"))) == D("109.50")


def test_percent_zero_rejected():
    with pytest.raises(ValueError):
        total([item("50.00")], make_coupon(value=D("0")))


def test_percent_negative_rejected():
    with pytest.raises(ValueError):
        total([item("50.00")], make_coupon(value=D("-1")))


def test_percent_over_100_rejected():
    with pytest.raises(ValueError):
        total([item("50.00")], make_coupon(value=D("100.01")))


# --- fixed coupons ---

def test_fixed_discount_applied():
    assert total([item("50.00")], make_coupon(kind="fixed", value=D("5"))) == D("55.00")


def test_fixed_discount_capped_at_subtotal():
    assert total([item("3.00")], make_coupon(kind="fixed", value=D("5"))) == D("10.00")


def test_fixed_discount_not_capped_when_below_subtotal():
    assert total([item("20.00")], make_coupon(kind="fixed", value=D("5"))) == D("25.00")


def test_fixed_zero_rejected():
    with pytest.raises(ValueError):
        total([item("50.00")], make_coupon(kind="fixed", value=D("0")))


def test_fixed_negative_rejected():
    with pytest.raises(ValueError):
        total([item("50.00")], make_coupon(kind="fixed", value=D("-2")))


# --- coupon validity ---

def test_coupon_expiring_today_is_accepted():
    coupon = make_coupon(expires=TODAY)
    assert total([item("50.00")], coupon) == D("50.00") * D("0.9") + D("10.00")


def test_coupon_expired_yesterday_rejected():
    coupon = make_coupon(expires=TODAY - timedelta(days=1))
    with pytest.raises(CouponError):
        total([item("50.00")], coupon)


def test_used_code_rejected():
    with pytest.raises(CouponError):
        total([item("50.00")], make_coupon(code="SAVE"), used={"SAVE"})


def test_other_used_code_does_not_block():
    assert total([item("50.00")], make_coupon(code="SAVE"), used={"OTHER"}) == D("55.00") + D("0")


def test_min_subtotal_equal_is_accepted():
    coupon = make_coupon(min_subtotal=D("50.00"))
    assert total([item("50.00")], coupon) == D("45.00") + D("10.00")


def test_below_min_subtotal_rejected():
    coupon = make_coupon(min_subtotal=D("50.01"))
    with pytest.raises(CouponError):
        total([item("50.00")], coupon)


def test_unknown_kind_rejected():
    with pytest.raises(CouponError):
        total([item("50.00")], make_coupon(kind="bogus"))


def test_coupon_error_is_a_value_error():
    assert issubclass(CouponError, ValueError)


# --- item validation ---

@pytest.mark.parametrize("qty", [0, -1, True, 1.0, "2"])
def test_invalid_quantity_rejected(qty):
    with pytest.raises(ValueError):
        total([("sku", D("1.00"), qty)])


def test_negative_price_rejected():
    with pytest.raises(ValueError):
        total([item("-0.01")])


def test_invalid_item_rejected_even_with_coupon():
    with pytest.raises(ValueError):
        total([item("-1.00")], make_coupon())


# --- rounding ---

def test_rounding_half_up():
    # 1.005 + 10 shipping = 11.005 -> 11.01 with ROUND_HALF_UP
    assert total([item("1.005")]) == D("11.01")


def test_result_has_two_decimal_places():
    result = total([item("1.00")])
    assert result == D("11.00")
    assert result.as_tuple().exponent == -2
