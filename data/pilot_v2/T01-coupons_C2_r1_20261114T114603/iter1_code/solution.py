from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


CENT = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")
SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")


def _subtotal(items: list[tuple[str, Decimal, int]]) -> Decimal:
    """Validate the items and return the sum of unit_price * quantity."""
    total = ZERO
    for sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"quantity for {sku!r} must be an integer >= 1, got {quantity!r}")
        if unit_price < 0:
            raise ValueError(f"unit_price for {sku!r} must be >= 0, got {unit_price!r}")
        total += unit_price * quantity
    return total


def _check_coupon(coupon: dict, subtotal: Decimal, today: date, used_codes: set[str]) -> None:
    """Raise CouponError if the coupon cannot be applied to this order."""
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError(f"unknown coupon kind {coupon['kind']!r}")
    if today > coupon["expires"]:
        raise CouponError("coupon has expired")
    if coupon["code"] in used_codes:
        raise CouponError("coupon already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError("subtotal is below the coupon minimum")


def _discount(coupon: dict, subtotal: Decimal) -> Decimal:
    """Return the discount amount for a valid coupon."""
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not (ZERO < value <= HUNDRED):
            raise ValueError(f"percent value must be in (0, 100], got {value!r}")
        return subtotal * value / HUNDRED
    if value <= 0:
        raise ValueError(f"fixed value must be > 0, got {value!r}")
    return min(value, subtotal)


def _shipping(items: list, amount: Decimal) -> Decimal:
    """Return the shipping cost for a discounted subtotal."""
    if not items:
        return ZERO
    if amount >= FREE_SHIPPING_THRESHOLD:
        return ZERO
    return SHIPPING_FEE


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _subtotal(items)
    discount = ZERO
    if coupon is not None:
        _check_coupon(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)
    amount = subtotal - discount
    total = amount + _shipping(items, amount)
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
