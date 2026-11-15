from datetime import date
from decimal import Decimal, ROUND_HALF_UP

SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
CENT = Decimal("0.01")
ZERO = Decimal("0")


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def _check_item(unit_price: Decimal, quantity: int) -> None:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise ValueError(f"quantity must be an integer >= 1, got {quantity!r}")
    if unit_price < 0:
        raise ValueError(f"unit_price must be >= 0, got {unit_price!r}")


def _subtotal(items: list[tuple[str, Decimal, int]]) -> Decimal:
    total = ZERO
    for _sku, unit_price, quantity in items:
        _check_item(unit_price, quantity)
        total += unit_price * quantity
    return total


def _check_coupon_usable(coupon: dict, subtotal: Decimal, today: date,
                         used_codes: set[str]) -> None:
    if coupon["expires"] < today:
        raise CouponError(f"coupon {coupon['code']} expired")
    if coupon["code"] in used_codes:
        raise CouponError(f"coupon {coupon['code']} already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError(f"subtotal below minimum for coupon {coupon['code']}")
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError(f"unknown coupon kind {coupon['kind']!r}")


def _discount(coupon: dict, subtotal: Decimal) -> Decimal:
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not ZERO < value <= Decimal("100"):
            raise ValueError(f"percent coupon value must be in (0, 100], got {value!r}")
        return subtotal * value / 100
    if value <= 0:
        raise ValueError(f"fixed coupon value must be > 0, got {value!r}")
    return min(value, subtotal)


def _shipping(items: list, discounted: Decimal) -> Decimal:
    if not items:
        return ZERO
    if discounted >= FREE_SHIPPING_THRESHOLD:
        return ZERO
    return SHIPPING_FEE


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _subtotal(items)
    discount = ZERO
    if coupon is not None:
        _check_coupon_usable(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)
    discounted = subtotal - discount
    total = discounted + _shipping(items, discounted)
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
