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
    # Rule 1: validate items.
    subtotal = Decimal("0")
    for _sku, unit_price, quantity in items:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"quantity must be an integer >= 1, got {quantity!r}")
        if not isinstance(unit_price, Decimal) or unit_price < 0:
            raise ValueError(f"unit_price must be a Decimal >= 0, got {unit_price!r}")
        # Rule 2: subtotal.
        subtotal += unit_price * quantity

    discount = Decimal("0")
    if coupon is not None:
        code = coupon["code"]
        kind = coupon["kind"]
        value = coupon["value"]
        min_subtotal = coupon["min_subtotal"]
        expires = coupon["expires"]

        # Rule 3: coupon validity.
        if today > expires:
            raise CouponError(f"coupon {code!r} expired on {expires}")
        if code in used_codes:
            raise CouponError(f"coupon {code!r} has already been used")
        if subtotal < min_subtotal:
            raise CouponError(f"subtotal {subtotal} is below minimum {min_subtotal} for coupon {code!r}")
        if kind not in ("percent", "fixed"):
            raise CouponError(f"unknown coupon kind {kind!r}")

        if kind == "percent":
            # Rule 4.
            if not (Decimal("0") < value <= Decimal("100")):
                raise ValueError(f"percent coupon value must be in (0, 100], got {value}")
            discount = subtotal * value / Decimal("100")
        else:
            # Rule 5.
            if not value > 0:
                raise ValueError(f"fixed coupon value must be > 0, got {value}")
            discount = min(value, subtotal)

    after_discount = subtotal - discount

    # Rule 6: shipping on the discounted subtotal; empty order has none.
    if not items:
        shipping = Decimal("0")
    elif after_discount < FREE_SHIPPING_THRESHOLD:
        shipping = SHIPPING_FEE
    else:
        shipping = Decimal("0")

    # Rule 7: round to cents, half up.
    total = after_discount + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
