from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 5, 1)


def cp(**kw):
    c = dict(code="A", kind="percent", value=D("10"), min_subtotal=D("0"), expires=TODAY)
    c.update(kw)
    return c


def test_empty():
    assert order_total([], None, TODAY, set()) == D("0.00")


def test_shipping_threshold():
    assert order_total([("a", D("99.99"), 1)], None, TODAY, set()) == D("109.99")
    assert order_total([("a", D("100"), 1)], None, TODAY, set()) == D("100.00")


def test_invalid_items():
    for item in [("a", D("1"), 0), ("a", D("1"), -1), ("a", D("-1"), 1), ("a", D("1"), 1.5)]:
        with pytest.raises(ValueError):
            order_total([item], None, TODAY, set())


def test_percent_and_shipping_after_discount():
    # 100 - 10% = 90 -> shipping 10
    assert order_total([("a", D("100"), 1)], cp(), TODAY, set()) == D("100.00")
    assert order_total([("a", D("200"), 1)], cp(), TODAY, set()) == D("180.00")


def test_fixed_capped():
    c = cp(kind="fixed", value=D("50"))
    assert order_total([("a", D("20"), 1)], c, TODAY, set()) == D("10.00")
    assert order_total([("a", D("200"), 1)], c, TODAY, set()) == D("150.00")


def test_rounding_half_up():
    assert order_total([("a", D("0.05"), 1)], cp(value=D("50")), TODAY, set()) == D("10.03")


def test_coupon_errors():
    items = [("a", D("50"), 1)]
    with pytest.raises(CouponError):
        order_total(items, cp(expires=date(2024, 4, 30)), TODAY, set())
    assert order_total(items, cp(), TODAY, set()) == D("55.00")
    with pytest.raises(CouponError):
        order_total(items, cp(), TODAY, {"A"})
    with pytest.raises(CouponError):
        order_total(items, cp(min_subtotal=D("50.01")), TODAY, set())
    order_total(items, cp(min_subtotal=D("50")), TODAY, set())
    with pytest.raises(CouponError):
        order_total(items, cp(kind="bogus"), TODAY, set())


def test_coupon_value_errors():
    items = [("a", D("50"), 1)]
    for c in [cp(value=D("0")), cp(value=D("101")), cp(kind="fixed", value=D("0")),
              cp(kind="fixed", value=D("-1"))]:
        with pytest.raises(ValueError):
            order_total(items, c, TODAY, set())
    assert order_total(items, cp(value=D("100")), TODAY, set()) == D("10.00")
