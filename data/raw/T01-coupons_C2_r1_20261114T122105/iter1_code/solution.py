from datetime import date
from decimal import Decimal, ROUND_HALF_UP

SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
CENTS = Decimal("0.01")


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def _validate_items(items: list[tuple[str, Decimal, int]]) -> None:
    for _sku, unit_price, quantity in items:
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise ValueError(f"quantity must be an integer >= 1, got {quantity!r}")
        if unit_price < 0:
            raise ValueError(f"unit_price must be >= 0, got {unit_price!r}")


def _subtotal(items: list[tuple[str, Decimal, int]]) -> Decimal:
    return sum((unit_price * quantity for _sku, unit_price, quantity in items), Decimal(0))


def _check_coupon_applicable(coupon: dict, subtotal: Decimal, today: date,
                             used_codes: set[str]) -> None:
    if today > coupon["expires"]:
        raise CouponError("coupon has expired")
    if coupon["code"] in used_codes:
        raise CouponError("coupon already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError("subtotal is below the coupon minimum")
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError(f"unknown coupon kind {coupon['kind']!r}")


def _discount(coupon: dict, subtotal: Decimal) -> Decimal:
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not 0 < value <= 100:
            raise ValueError(f"percent coupon value must be in (0, 100], got {value!r}")
        return subtotal * value / 100
    if value <= 0:
        raise ValueError(f"fixed coupon value must be > 0, got {value!r}")
    return min(value, subtotal)


def _shipping(items: list[tuple[str, Decimal, int]], net: Decimal) -> Decimal:
    if not items:
        return Decimal(0)
    if net >= FREE_SHIPPING_THRESHOLD:
        return Decimal(0)
    return SHIPPING_FEE


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    _validate_items(items)
    subtotal = _subtotal(items)
    discount = Decimal(0)
    if coupon is not None:
        _check_coupon_applicable(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)
    net = subtotal - discount
    total = net + _shipping(items, net)
    return total.quantize(CENTS, rounding=ROUND_HALF_UP)
