from datetime import date
from decimal import ROUND_HALF_UP, Decimal

SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
HUNDRED = Decimal(100)
CENT = Decimal("0.01")


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def _subtotal(items: list[tuple[str, Decimal, int]]) -> Decimal:
    total = Decimal(0)
    for sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"invalid quantity for {sku!r}: {quantity!r}")
        if not isinstance(unit_price, Decimal) or unit_price < 0:
            raise ValueError(f"invalid unit price for {sku!r}: {unit_price!r}")
        total += unit_price * quantity
    return total


def _check_coupon(coupon: dict, subtotal: Decimal, today: date, used_codes: set[str]) -> None:
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError(f"unknown coupon kind: {coupon['kind']!r}")
    if today > coupon["expires"]:
        raise CouponError(f"coupon {coupon['code']!r} expired")
    if coupon["code"] in used_codes:
        raise CouponError(f"coupon {coupon['code']!r} already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError(f"subtotal below minimum for coupon {coupon['code']!r}")


def _discount(coupon: dict, subtotal: Decimal) -> Decimal:
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not Decimal(0) < value <= HUNDRED:
            raise ValueError(f"percent value must be in (0, 100], got {value!r}")
        return subtotal * value / HUNDRED
    if value <= 0:
        raise ValueError(f"fixed value must be positive, got {value!r}")
    return min(value, subtotal)


def _shipping(discounted: Decimal, items: list[tuple[str, Decimal, int]]) -> Decimal:
    if not items:
        return Decimal(0)
    if discounted >= FREE_SHIPPING_THRESHOLD:
        return Decimal(0)
    return SHIPPING_FEE


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _subtotal(items)
    discount = Decimal(0)
    if coupon is not None:
        _check_coupon(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)
    discounted = subtotal - discount
    total = discounted + _shipping(discounted, items)
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
