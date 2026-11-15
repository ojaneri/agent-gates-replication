from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = Decimal(0)
    for _sku, price, qty in items:
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("quantity must be an integer >= 1")
        if price < 0:
            raise ValueError("unit_price must be >= 0")
        subtotal += price * qty

    discount = Decimal(0)
    if coupon is not None:
        if today > coupon["expires"]:
            raise CouponError("coupon expired")
        if coupon["code"] in used_codes:
            raise CouponError("coupon already used")
        if subtotal < coupon["min_subtotal"]:
            raise CouponError("subtotal below minimum")
        kind = coupon["kind"]
        value = coupon["value"]
        if kind == "percent":
            if not (0 < value <= 100):
                raise ValueError("invalid percent value")
            discount = subtotal * value / 100
        elif kind == "fixed":
            if not value > 0:
                raise ValueError("invalid fixed value")
            discount = min(value, subtotal)
        else:
            raise CouponError("unknown coupon kind")

    after = subtotal - discount
    shipping = Decimal(0)
    if items and after < Decimal("100.00"):
        shipping = Decimal("10.00")
    return (after + shipping).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
