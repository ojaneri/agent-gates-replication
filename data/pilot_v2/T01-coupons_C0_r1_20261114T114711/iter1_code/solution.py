from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


CENT = Decimal("0.01")
SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")


def _validate_items(items: list[tuple[str, Decimal, int]]) -> Decimal:
    """Validate items and return their subtotal."""
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


def _discount(coupon: dict | None, subtotal: Decimal) -> Decimal:
    """Return the discount amount for the coupon (zero when there is no coupon)."""
    if coupon is None:
        return Decimal("0")
    value = coupon["value"]
    if coupon["kind"] == "percent":
        if not (0 < value <= 100):
            raise ValueError(f"percent coupon value must be in (0, 100], got {value}")
        return subtotal * value / Decimal("100")
    # kind == "fixed" (kind was validated earlier)
    if value <= 0:
        raise ValueError(f"fixed coupon value must be > 0, got {value}")
    return min(value, subtotal)


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    subtotal = _validate_items(items)

    if coupon is not None:
        _check_coupon_validity(coupon, subtotal, today, used_codes)

    discount = _discount(coupon, subtotal)
    after_discount = subtotal - discount

    if not items:
        shipping = Decimal("0")
    elif after_discount < FREE_SHIPPING_THRESHOLD:
        shipping = SHIPPING_FEE
    else:
        shipping = Decimal("0")

    total = after_discount + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
