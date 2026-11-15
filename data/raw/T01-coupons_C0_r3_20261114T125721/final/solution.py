from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


CENT = Decimal("0.01")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
SHIPPING_COST = Decimal("10.00")


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    # Rule 1: validate items.
    for _sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError("quantity must be an integer of at least 1")
        if unit_price < 0:
            raise ValueError("unit_price must be at least 0")

    # Rule 2: subtotal.
    subtotal = sum((Decimal(unit_price) * quantity for _sku, unit_price, quantity in items),
                   Decimal(0))

    # Rule 3 & 4 & 5: coupon handling.
    discount = Decimal(0)
    if coupon is not None:
        expires = coupon["expires"]
        code = coupon["code"]
        kind = coupon["kind"]
        value = Decimal(coupon["value"])
        min_subtotal = Decimal(coupon["min_subtotal"])

        if today > expires:
            raise CouponError("coupon has expired")
        if code in used_codes:
            raise CouponError("coupon has already been used")
        if subtotal < min_subtotal:
            raise CouponError("subtotal is below the coupon minimum")
        if kind not in ("percent", "fixed"):
            raise CouponError("unknown coupon kind")

        if kind == "percent":
            if not (Decimal(0) < value <= Decimal(100)):
                raise ValueError("percent coupon value must be in (0, 100]")
            discount = subtotal * value / Decimal(100)
        else:
            if not value > 0:
                raise ValueError("fixed coupon value must be positive")
            discount = min(value, subtotal)

    # Rule 6: shipping on the discounted subtotal.
    after_discount = subtotal - discount
    if not items:
        shipping = Decimal(0)
    elif after_discount < FREE_SHIPPING_THRESHOLD:
        shipping = SHIPPING_COST
    else:
        shipping = Decimal(0)

    # Rule 7: final rounding.
    total = after_discount + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
