from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
CENT = Decimal("0.01")


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    # Rule 1: validate line items.
    for sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"quantity must be an integer >= 1, got {quantity!r} for {sku!r}")
        if unit_price < 0:
            raise ValueError(f"unit_price must be >= 0, got {unit_price!r} for {sku!r}")

    # Rule 2: subtotal.
    subtotal = sum((unit_price * quantity for _, unit_price, quantity in items), Decimal("0"))

    # Rule 3 (and value checks from rules 4 and 5): coupon.
    discount = Decimal("0")
    if coupon is not None:
        code = coupon["code"]
        kind = coupon["kind"]
        value = coupon["value"]
        expires = coupon["expires"]
        min_subtotal = coupon["min_subtotal"]

        if today > expires:
            raise CouponError(f"coupon {code!r} expired on {expires}")
        if code in used_codes:
            raise CouponError(f"coupon {code!r} was already used")
        if subtotal < min_subtotal:
            raise CouponError(
                f"subtotal {subtotal} is below the coupon minimum {min_subtotal}")
        if kind not in ("percent", "fixed"):
            raise CouponError(f"unknown coupon kind {kind!r}")

        if kind == "percent":
            if not (Decimal("0") < value <= Decimal("100")):
                raise ValueError(f"percent value must satisfy 0 < value <= 100, got {value}")
            discount = subtotal * value / Decimal("100")
        else:  # fixed
            if not value > 0:
                raise ValueError(f"fixed value must be > 0, got {value}")
            discount = min(value, subtotal)

    # Rule 6: shipping on the discounted subtotal; empty order has no shipping.
    discounted = subtotal - discount
    if not items:
        shipping = Decimal("0")
    elif discounted < FREE_SHIPPING_THRESHOLD:
        shipping = SHIPPING_FEE
    else:
        shipping = Decimal("0")

    # Rule 7: round to cents, halves up.
    total = discounted + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
