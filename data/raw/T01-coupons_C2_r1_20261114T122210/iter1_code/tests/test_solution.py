from datetime import date
from decimal import Decimal as D

import pytest

from solution import CouponError, order_total

TODAY = date(2024, 5, 10)


def coupon(**kw):
    c = {"code": "A", "kind": "percent", "value": D("10"),
         "min_subtotal": D("0"), "expires": TODAY}
    c.update(kw)
    return c


def run(items, c=None, used=frozenset()):
    return order_total(items, c, TODAY, set(used))


def test_empty():
    assert run([]) == D("0.00")


def test_empty_with_coupon():
    assert run([], coupon()) == D("0.00")


def test_shipping_below_and_at_threshold():
    assert run([("a", D("99.99"), 1)]) == D("109.99")
    assert run([("a", D("100.00"), 1)]) == D("100.00")


def test_quantity_multiplies():
    assert run([("a", D("30"), 2), ("b", D("20"), 2)]) == D("100.00")


def test_zero_price_item_has_shipping():
    assert run([("a", D("0"), 1)]) == D("10.00")


def test_invalid_items():
    for q in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            run([("a", D("1"), q)])
    with pytest.raises(ValueError):
        run([("a", D("-0.01"), 1)])


def test_percent():
    assert run([("a", D("200"), 1)], coupon()) == D("180.00")


def test_percent_shipping_after_discount():
    assert run([("a", D("100"), 1)], coupon()) == D("100.00")


def test_percent_100():
    assert run([("a", D("50"), 1)], coupon(value=D("100"))) == D("10.00")


def test_rounding_half_up():
    assert run([("a", D("100.005"), 1)]) == D("100.01")
    assert run([("a", D("100.004"), 1)]) == D("100.00")


def test_fixed():
    c = coupon(kind="fixed", value=D("30"))
    assert run([("a", D("200"), 1)], c) == D("170.00")


def test_fixed_capped():
    c = coupon(kind="fixed", value=D("500"))
    assert run([("a", D("50"), 1)], c) == D("10.00")


def test_expiry_boundary():
    assert run([("a", D("200"), 1)], coupon(expires=TODAY)) == D("180.00")
    with pytest.raises(CouponError):
        run([("a", D("200"), 1)], coupon(expires=date(2024, 5, 9)))


def test_used_code():
    with pytest.raises(CouponError):
        run([("a", D("200"), 1)], coupon(), used={"A"})
    assert run([("a", D("200"), 1)], coupon(), used={"B"}) == D("180.00")


def test_min_subtotal():
    c = coupon(min_subtotal=D("200"))
    assert run([("a", D("200"), 1)], c) == D("180.00")
    with pytest.raises(CouponError):
        run([("a", D("199.99"), 1)], c)


def test_bad_kind():
    with pytest.raises(CouponError):
        run([("a", D("200"), 1)], coupon(kind="bogus"))


def test_bad_values():
    items = [("a", D("200"), 1)]
    for v in (D("0"), D("100.01"), D("-1")):
        with pytest.raises(ValueError):
            run(items, coupon(value=v))
    for v in (D("0"), D("-5")):
        with pytest.raises(ValueError):
            run(items, coupon(kind="fixed", value=v))
