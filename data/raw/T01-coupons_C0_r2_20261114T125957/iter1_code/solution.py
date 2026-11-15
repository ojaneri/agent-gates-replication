from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


SHIPPING_FEE = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")
CENT = Decimal("0.01")


def _is_int(value) -> bool:
    # bool is a subclass of int, but True/False are not valid quantities.
    return isinstance(value, int) and not isinstance(value, bool)


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    # Rule 1 and 2: validate items and compute the subtotal.
    subtotal = Decimal("0")
    for _sku, unit_price, quantity in items:
        if not _is_int(quantity) or quantity < 1:
            raise ValueError(f"quantity must be an integer >= 1, got {quantity!r}")
        if unit_price < 0:
            raise ValueError(f"unit_price must be >= 0, got {unit_price!r}")
        subtotal += unit_price * quantity

    # Rule 3, 4, 5: coupon validity and discount.
    discount = Decimal("0")
    if coupon is not None:
        code = coupon["code"]
        kind = coupon["kind"]
        value = coupon["value"]
        min_subtotal = coupon["min_subtotal"]
        expires = coupon["expires"]

        if today > expires:
            raise CouponError(f"coupon {code!r} expired on {expires}")
        if code in used_codes:
            raise CouponError(f"coupon {code!r} was already used")
        if subtotal < min_subtotal:
            raise CouponError(f"subtotal {subtotal} is below minimum {min_subtotal}")
        if kind not in ("percent", "fixed"):
            raise CouponError(f"unknown coupon kind {kind!r}")

        if kind == "percent":
            if not (0 < value <= 100):
                raise ValueError(f"percent value must be in (0, 100], got {value}")
            discount = subtotal * value / 100
        else:  # fixed
            if value <= 0:
                raise ValueError(f"fixed value must be > 0, got {value}")
            discount = min(value, subtotal)

    # Rule 6: shipping is based on the subtotal after discount.
    after_discount = subtotal - discount
    if not items:
        shipping = Decimal("0")
    elif after_discount >= FREE_SHIPPING_THRESHOLD:
        shipping = Decimal("0")
    else:
        shipping = SHIPPING_FEE

    # Rule 7: round to 2 decimal places, halves up.
    total = after_discount + shipping
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
