from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


CENT = Decimal("0.01")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
SHIPPING_FEE = Decimal("10.00")


def _validate_items(items: list[tuple[str, Decimal, int]]) -> Decimal:
    """Validate line items and return the subtotal."""
    subtotal = Decimal("0")
    for _sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"quantity must be an integer >= 1, got {quantity!r}")
        if unit_price < 0:
            raise ValueError(f"unit_price must be >= 0, got {unit_price!r}")
        subtotal += unit_price * quantity
    return subtotal


def _check_coupon_validity(coupon: dict, subtotal: Decimal, today: date,
                           used_codes: set[str]) -> None:
    """Raise CouponError if the coupon cannot be applied to this order."""
    if today > coupon["expires"]:
        raise CouponError(f"coupon {coupon['code']!r} has expired")
    if coupon["code"] in used_codes:
        raise CouponError(f"coupon {coupon['code']!r} was already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError(
            f"subtotal {subtotal} is below the coupon minimum {coupon['min_subtotal']}")
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError(f"unknown coupon kind {coupon['kind']!r}")


def _discount(coupon: dict, subtotal: Decimal) -> Decimal:
    """Return the discount amount for a valid coupon."""
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not (Decimal("0") < value <= Decimal("100")):
            raise ValueError(f"percent coupon value must be in (0, 100], got {value}")
        return subtotal * value / Decimal("100")
    if value <= 0:
        raise ValueError(f"fixed coupon value must be > 0, got {value}")
    return min(value, subtotal)


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _validate_items(items)

    discount = Decimal("0")
    if coupon is not None:
        _check_coupon_validity(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)

    discounted = subtotal - discount

    if not items:
        shipping = Decimal("0")
    elif discounted < FREE_SHIPPING_THRESHOLD:
        shipping = SHIPPING_FEE
    else:
        shipping = Decimal("0")

    total = discounted + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
