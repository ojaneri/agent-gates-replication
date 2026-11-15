from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def _subtotal(items) -> Decimal:
    total = Decimal(0)
    for _sku, price, qty in items:
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("invalid quantity")
        if price < 0:
            raise ValueError("invalid unit price")
        total += price * qty
    return total


def _check_coupon(coupon, subtotal, today, used_codes) -> None:
    if today > coupon["expires"]:
        raise CouponError("expired")
    if coupon["code"] in used_codes:
        raise CouponError("already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError("subtotal too low")
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError("unknown kind")


def _discount(coupon, subtotal) -> Decimal:
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not 0 < value <= 100:
            raise ValueError("invalid percent")
        return subtotal * value / 100
    if value <= 0:
        raise ValueError("invalid fixed value")
    return min(value, subtotal)


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _subtotal(items)
    discount = Decimal(0)
    if coupon is not None:
        _check_coupon(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)
    after = subtotal - discount
    shipping = Decimal(0)
    if items and after < 100:
        shipping = Decimal(10)
    return (after + shipping).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
