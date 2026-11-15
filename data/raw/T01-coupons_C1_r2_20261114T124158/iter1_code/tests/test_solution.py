from datetime import date
from decimal import Decimal

import pytest

from solution import CouponError, order_total

TODAY = date(2026, 6, 15)
D = Decimal


def coupon(kind="percent", value=D("10"), min_subtotal=D("0"),
           expires=date(2026, 12, 31), code="SAVE"):
    return {"code": code, "kind": kind, "value": value,
            "min_subtotal": min_subtotal, "expires": expires}


# --- basic totals and shipping ---

def test_empty_order_has_no_shipping():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_below_threshold_pays_shipping():
    assert order_total([("a", D("20.00"), 2)], None, TODAY, set()) == D("50.00")


def test_exactly_100_ships_free():
    assert order_total([("a", D("50.00"), 2)], None, TODAY, set()) == D("100.00")


def test_above_threshold_ships_free():
    assert order_total([("a", D("99.99"), 2)], None, TODAY, set()) == D("199.98")


def test_multiple_items_summed():
    items = [("a", D("10.00"), 3), ("b", D("5.50"), 2), ("c", D("100.00"), 1)]
    assert order_total(items, None, TODAY, set()) == D("141.00")


def test_zero_price_item_still_pays_shipping():
    # Items present, subtotal 0: not an empty order, so shipping applies.
    assert order_total([("free", D("0"), 1)], None, TODAY, set()) == D("10.00")


# --- rule 1: item validation ---

@pytest.mark.parametrize("qty", [0, -1])
def test_quantity_below_one_rejected(qty):
    with pytest.raises(ValueError):
        order_total([("a", D("1"), qty)], None, TODAY, set())


@pytest.mark.parametrize("qty", [1.5, "2", None, True])
def test_non_integer_quantity_rejected(qty):
    with pytest.raises(ValueError):
        order_total([("a", D("1"), qty)], None, TODAY, set())


def test_negative_price_rejected():
    with pytest.raises(ValueError):
        order_total([("a", D("-0.01"), 1)], None, TODAY, set())


def test_zero_price_accepted():
    assert order_total([("a", D("0"), 1)], None, TODAY, set()) == D("10.00")


# --- rule 3: coupon validity ---

def test_expired_coupon_rejected():
    with pytest.raises(CouponError):
        order_total([("a", D("100"), 1)],
                    coupon(expires=date(2026, 6, 14)), TODAY, set())


def test_coupon_valid_on_expiry_date():
    total = order_total([("a", D("100"), 1)],
                        coupon(expires=TODAY), TODAY, set())
    # 100 - 10% = 90 (below 100, shipping 10) -> 100.00
    assert total == D("100.00")


def test_already_used_code_rejected():
    with pytest.raises(CouponError):
        order_total([("a", D("100"), 1)], coupon(code="SAVE"), TODAY, {"SAVE"})


def test_other_used_code_does_not_block():
    total = order_total([("a", D("100"), 1)], coupon(code="NEW"), TODAY, {"OLD"})
    assert total == D("100.00")


def test_min_subtotal_not_met_rejected():
    with pytest.raises(CouponError):
        order_total([("a", D("49.99"), 1)],
                    coupon(min_subtotal=D("50")), TODAY, set())


def test_min_subtotal_equal_accepted():
    total = order_total([("a", D("50"), 1)],
                        coupon(min_subtotal=D("50")), TODAY, set())
    assert total == D("55.00")  # 45 discounted, shipping 10


def test_unknown_kind_rejected():
    with pytest.raises(CouponError):
        order_total([("a", D("100"), 1)], coupon(kind="bogus"), TODAY, set())


# --- rule 4: percent coupons ---

def test_percent_discount():
    # 100 - 25% = 75, shipping 10 -> 85
    total = order_total([("a", D("100"), 1)],
                        coupon(kind="percent", value=D("25")), TODAY, set())
    assert total == D("85.00")


def test_percent_100_gives_free_order_with_shipping_on_zero():
    total = order_total([("a", D("100"), 1)],
                        coupon(kind="percent", value=D("100")), TODAY, set())
    # discounted subtotal 0 is below 100, so shipping of 10 applies
    assert total == D("10.00")


@pytest.mark.parametrize("value", [D("0"), D("-5"), D("100.01"), D("150")])
def test_invalid_percent_value_rejected(value):
    with pytest.raises(ValueError):
        order_total([("a", D("100"), 1)],
                    coupon(kind="percent", value=value), TODAY, set())


# --- rule 5: fixed coupons ---

def test_fixed_discount():
    total = order_total([("a", D("120"), 1)],
                        coupon(kind="fixed", value=D("20")), TODAY, set())
    assert total == D("100.00")


def test_fixed_discount_capped_at_subtotal():
    total = order_total([("a", D("30"), 1)],
                        coupon(kind="fixed", value=D("50")), TODAY, set())
    # discount capped at 30 -> subtotal 0 -> shipping 10
    assert total == D("10.00")


@pytest.mark.parametrize("value", [D("0"), D("-1")])
def test_invalid_fixed_value_rejected(value):
    with pytest.raises(ValueError):
        order_total([("a", D("100"), 1)],
                    coupon(kind="fixed", value=value), TODAY, set())


# --- rule 6: shipping uses discounted subtotal ---

def test_discount_drops_subtotal_below_threshold_so_shipping_applies():
    # 110 - 10% = 99 -> below 100 -> shipping 10 -> 109
    total = order_total([("a", D("110"), 1)],
                        coupon(kind="percent", value=D("10")), TODAY, set())
    assert total == D("109.00")


def test_discount_keeps_subtotal_at_threshold_free_shipping():
    # 111.11 - 10% = 99.999 ... pick numbers landing exactly on 100
    total = order_total([("a", D("125"), 1)],
                        coupon(kind="percent", value=D("20")), TODAY, set())
    assert total == D("100.00")


# --- rule 7: rounding ---

def test_result_rounded_half_up():
    # 10.00 * 0.125 discount: 10 - 1.25 = 8.75, + shipping 10 = 18.75 (exact)
    # use a discount that yields a third-of-cent: 0.01 * 1/3 style
    total = order_total([("a", D("0.05"), 1)],
                        coupon(kind="percent", value=D("50")), TODAY, set())
    # 0.05 - 0.025 = 0.025 -> shipping 10 -> 10.025 -> half-up -> 10.03
    assert total == D("10.03")


def test_result_rounding_down_case():
    total = order_total([("a", D("0.04"), 1)],
                        coupon(kind="percent", value=D("50")), TODAY, set())
    # 0.04 - 0.02 = 0.02 -> +10 -> 10.02
    assert total == D("10.02")


def test_result_has_two_decimal_places():
    total = order_total([("a", D("100"), 1)], None, TODAY, set())
    assert total == D("100.00")
    assert total.as_tuple().exponent == -2
