from datetime import date
from decimal import Decimal


class CouponError(ValueError):
    """Raised when a coupon cannot be applied."""


def order_total(items: list[tuple[str, Decimal, int]], coupon: dict | None, today: date,
                used_codes: set[str]) -> Decimal:
    """Return the order total. See spec.md for the rules."""
    raise NotImplementedError
