from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
CENT = Decimal("0.01")


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


def _validate_coupon(coupon: dict, subtotal: Decimal, today: date,
                     used_codes: set[str]) -> None:
    """Raise CouponError if the coupon cannot be applied at all."""
    if today > coupon["expires"]:
        raise CouponError(f"coupon {coupon['code']!r} has expired")
    if coupon["code"] in used_codes:
        raise CouponError(f"coupon {coupon['code']!r} was already used")
    if subtotal < coupon["min_subtotal"]:
        raise CouponError(
            f"subtotal {subtotal} is below the minimum {coupon['min_subtotal']} "
            f"for coupon {coupon['code']!r}")
    if coupon["kind"] not in ("percent", "fixed"):
        raise CouponError(f"unknown coupon kind {coupon['kind']!r}")


def _discount(coupon: dict, subtotal: Decimal) -> Decimal:
    """Compute the discount amount for a valid coupon."""
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not (Decimal("0") < value <= Decimal("100")):
            raise ValueError(f"percent value must be in (0, 100], got {value!r}")
        return subtotal * value / Decimal("100")
    # fixed
    if not value > 0:
        raise ValueError(f"fixed value must be > 0, got {value!r}")
    return min(value, subtotal)


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _validate_items(items)

    discount = Decimal("0")
    if coupon is not None:
        _validate_coupon(coupon, subtotal, today, used_codes)
        discount = _discount(coupon, subtotal)

    after_discount = subtotal - discount
    if not items:
        shipping = Decimal("0")
    elif after_discount >= FREE_SHIPPING_THRESHOLD:
        shipping = Decimal("0")
    else:
        shipping = SHIPPING_FEE

    total = after_discount + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
