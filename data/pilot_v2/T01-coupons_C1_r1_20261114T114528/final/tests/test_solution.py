from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 5, 1)


def coup(**kw):
    c = {"code": "C1", "kind": "percent", "value": D("10"), "min_subtotal": D("0"),
         "expires": TODAY}
    c.update(kw)
    return c


def test_no_coupon_shipping():
    assert order_total([("a", D("10.00"), 2)], None, TODAY, set()) == D("30.00")


def test_free_shipping_threshold():
    assert order_total([("a", D("100.00"), 1)], None, TODAY, set()) == D("100.00")


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")
    assert order_total([], coup(kind="fixed", value=D("5")), TODAY, set()) == D("0.00")


@pytest.mark.parametrize("qty", [0, -1, 1.5, True])
def test_bad_qty(qty):
    with pytest.raises(ValueError):
        order_total([("a", D("1"), qty)], None, TODAY, set())


def test_bad_price():
    with pytest.raises(ValueError):
        order_total([("a", D("-1"), 1)], None, TODAY, set())


def test_percent_discount_and_shipping_after():
    # 110 - 10% = 99 -> shipping 10
    assert order_total([("a", D("110"), 1)], coup(), TODAY, set()) == D("109.00")


def test_percent_free_shipping():
    assert order_total([("a", D("200"), 1)], coup(), TODAY, set()) == D("180.00")


def test_rounding_half_up():
    assert order_total([("a", D("100.05"), 1)], coup(value=D("50")), TODAY, set()) == D("60.03")
    assert order_total([("a", D("0.05"), 1)], None, TODAY, set()) == D("10.05")
    assert order_total([("a", D("100.01"), 1)], coup(value=D("50")), TODAY, set()) == D("60.01")


def test_fixed_and_cap():
    assert order_total([("a", D("150"), 1)], coup(kind="fixed", value=D("20")), TODAY, set()) == D("130.00")
    assert order_total([("a", D("5"), 1)], coup(kind="fixed", value=D("20")), TODAY, set()) == D("10.00")


def test_expired_and_boundary():
    with pytest.raises(CouponError):
        order_total([("a", D("5"), 1)], coup(expires=date(2024, 4, 30)), TODAY, set())
    order_total([("a", D("5"), 1)], coup(expires=TODAY), TODAY, set())


def test_used():
    with pytest.raises(CouponError):
        order_total([("a", D("5"), 1)], coup(), TODAY, {"C1"})


def test_min_subtotal():
    with pytest.raises(CouponError):
        order_total([("a", D("5"), 1)], coup(min_subtotal=D("5.01")), TODAY, set())
    order_total([("a", D("5"), 1)], coup(min_subtotal=D("5")), TODAY, set())


def test_unknown_kind():
    with pytest.raises(CouponError):
        order_total([("a", D("5"), 1)], coup(kind="bogus"), TODAY, set())


@pytest.mark.parametrize("kind,value", [("percent", D("0")), ("percent", D("101")),
                                        ("fixed", D("0")), ("fixed", D("-1"))])
def test_bad_values(kind, value):
    with pytest.raises(ValueError):
        order_total([("a", D("5"), 1)], coup(kind=kind, value=value), TODAY, set())


def test_percent_100():
    assert order_total([("a", D("50"), 1)], coup(value=D("100")), TODAY, set()) == D("10.00")
