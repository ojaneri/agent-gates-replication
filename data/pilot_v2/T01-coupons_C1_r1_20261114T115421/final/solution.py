from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
SHIPPING_COST = Decimal("10.00")


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def _validate_items(items: list[tuple[str, Decimal, int]]) -> Decimal:
    """Validate each line item and return the subtotal."""
    subtotal = Decimal("0")
    for _sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"quantity must be an integer >= 1, got {quantity!r}")
        if unit_price < 0:
            raise ValueError(f"unit_price must be >= 0, got {unit_price!r}")
        subtotal += unit_price * quantity
    return subtotal


def _check_coupon_validity(coupon: dict, today: date, subtotal: Decimal,
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


def _discount(coupon: dict | None, subtotal: Decimal) -> Decimal:
    """Return the discount amount for the coupon (zero if there is none)."""
    if coupon is None:
        return Decimal("0")
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not (0 < value <= 100):
            raise ValueError(f"percent value must be in (0, 100], got {value}")
        return subtotal * value / 100
    # fixed
    if value <= 0:
        raise ValueError(f"fixed value must be > 0, got {value}")
    return min(value, subtotal)


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _validate_items(items)

    discount = Decimal("0")
    if coupon is not None:
        _check_coupon_validity(coupon, today, subtotal, used_codes)
        discount = _discount(coupon, subtotal)

    after_discount = subtotal - discount

    if not items:
        shipping = Decimal("0")
    elif after_discount < FREE_SHIPPING_THRESHOLD:
        shipping = SHIPPING_COST
    else:
        shipping = Decimal("0")

    total = after_discount + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
