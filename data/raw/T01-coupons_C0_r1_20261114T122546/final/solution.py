from datetime import date
from decimal import Decimal


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    from decimal import ROUND_HALF_UP
    for _sku, price, qty in items:
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("invalid quantity")
        if price < 0:
            raise ValueError("invalid unit price")
    subtotal = sum((p * q for _s, p, q in items), Decimal(0))
    discount = Decimal(0)
    if coupon is not None:
        if today > coupon["expires"]:
            raise CouponError("expired")
        if coupon["code"] in used_codes:
            raise CouponError("already used")
        if subtotal < coupon["min_subtotal"]:
            raise CouponError("subtotal too low")
        kind = coupon["kind"]
        value = coupon["value"]
        if kind == "percent":
            if not (0 < value <= 100):
                raise ValueError("invalid percent")
            discount = subtotal * value / 100
        elif kind == "fixed":
            if not value > 0:
                raise ValueError("invalid fixed value")
            discount = min(value, subtotal)
        else:
            raise CouponError("unknown kind")
    after = subtotal - discount
    shipping = Decimal(0)
    if items and after < Decimal("100.00"):
        shipping = Decimal("10.00")
    return (after + shipping).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
