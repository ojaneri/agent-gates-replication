from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
CENTS = Decimal("0.01")


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    # Rule 1: validate items and compute subtotal (rule 2).
    subtotal = Decimal("0")
    for _sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"quantity must be an integer >= 1, got {quantity!r}")
        if unit_price < 0:
            raise ValueError(f"unit_price must be >= 0, got {unit_price!r}")
        subtotal += unit_price * quantity

    discount = Decimal("0")
    if coupon is not None:
        code = coupon["code"]
        kind = coupon["kind"]
        value = coupon["value"]
        min_subtotal = coupon["min_subtotal"]
        expires = coupon["expires"]

        # Rule 3: coupon validity.
        if kind not in ("percent", "fixed"):
            raise CouponError(f"unknown coupon kind: {kind!r}")
        if today > expires:
            raise CouponError(f"coupon {code!r} expired on {expires}")
        if code in used_codes:
            raise CouponError(f"coupon {code!r} already used")
        if subtotal < min_subtotal:
            raise CouponError(f"subtotal {subtotal} below minimum {min_subtotal} for coupon {code!r}")

        # Rules 4 and 5: discount computation.
        if kind == "percent":
            if not (Decimal("0") < value <= Decimal("100")):
                raise ValueError(f"percent value must be in (0, 100], got {value!r}")
            discount = subtotal * value / Decimal("100")
        else:
            if not value > 0:
                raise ValueError(f"fixed value must be > 0, got {value!r}")
            discount = min(value, subtotal)

    discounted = subtotal - discount

    # Rule 6: shipping on the discounted subtotal; empty order has no shipping.
    if not items:
        shipping = Decimal("0")
    elif discounted < FREE_SHIPPING_THRESHOLD:
        shipping = SHIPPING_FEE
    else:
        shipping = Decimal("0")

    # Rule 7: round to cents, halves up.
    total = discounted + shipping
    return total.quantize(CENTS, rounding=ROUND_HALF_UP)
