from datetime import date
from decimal import Decimal, ROUND_HALF_UP

SHIPPING = Decimal("10.00")
FREE_SHIPPING_FROM = Decimal("100.00")
CENT = Decimal("0.01")


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def _subtotal(items):
    total = Decimal("0")
    for _sku, price, qty in items:
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
            raise ValueError("quantity must be an integer >= 1")
        if price < 0:
            raise ValueError("unit price must be >= 0")
        total += price * qty
    return total


def _check_coupon(coupon, subtotal, today, used_codes):
    if today > coupon["expires"]:
        raise CouponError("coupon expired")
    if coupon["code"] in used_codes:
        raise CouponError("coupon already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError("subtotal below coupon minimum")
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError("unknown coupon kind")


def _discount(coupon, subtotal):
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not (0 < value <= 100):
            raise ValueError("percent must be in (0, 100]")
        return subtotal * value / 100
    if value <= 0:
        raise ValueError("fixed discount must be > 0")
    return min(value, subtotal)


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    subtotal = _subtotal(items)
    discount = Decimal("0")
    if coupon is not None:
        _check_coupon(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)
    after = subtotal - discount
    shipping = Decimal("0") if not items or after >= FREE_SHIPPING_FROM else SHIPPING
    return (after + shipping).quantize(CENT, rounding=ROUND_HALF_UP)
