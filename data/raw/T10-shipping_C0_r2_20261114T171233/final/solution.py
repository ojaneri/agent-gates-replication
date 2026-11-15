from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

_BASE_FIRST_KG = Decimal("8.00")
_PER_HALF_KG = Decimal("1.50")
_VOLUME_DIVISOR = Decimal("5000")
_OVERSIZE_CM = Decimal("120")
_OVERSIZE_SURCHARGE = Decimal("12.00")
_FREE_SHIPPING_SUBTOTAL = Decimal("150")
_ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
_CENT = Decimal("0.01")


def _to_decimal(value) -> Decimal:
    """Convert a number to Decimal; raise TypeError for non-numbers, ValueError for NaN/inf."""
    if isinstance(value, bool):
        raise TypeError("bool is not a valid number here")
    if isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, float):
        number = Decimal(str(value))
    elif isinstance(value, Decimal):
        number = value
    else:
        raise TypeError(f"expected int, float or Decimal, got {type(value).__name__}")
    if not number.is_finite():
        raise ValueError("value must be finite")
    return number


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm)
    width = _to_decimal(width_cm)
    height = _to_decimal(height_cm)
    weight = _to_decimal(weight_kg)
    amount = _to_decimal(subtotal)

    if length <= 0 or width <= 0 or height <= 0 or weight <= 0:
        raise ValueError("dimensions and weight must be greater than zero")
    if amount < 0:
        raise ValueError("subtotal must be zero or more")
    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be the int 1, 2 or 3")

    # Rule 1-2: billable weight, rounded up to the next multiple of 0.5 kg.
    volumetric = length * width * height / _VOLUME_DIVISOR
    actual_billable = max(weight, volumetric)
    half_kg_steps = (actual_billable * 2).to_integral_value(rounding=ROUND_CEILING)
    billable = half_kg_steps / 2

    # Rule 3: 8.00 for the first kg, plus 1.50 per further 0.5 kg.
    extra_half_kgs = max(Decimal(0), half_kg_steps - 2)
    base = _BASE_FIRST_KG + _PER_HALF_KG * extra_half_kgs

    # Rule 4: zone factor.
    base *= _ZONE_FACTORS[zone]

    # Rule 5: free shipping for zones 1 and 2 at a subtotal of 150 or more.
    if amount >= _FREE_SHIPPING_SUBTOTAL and zone in (1, 2):
        base = Decimal(0)

    # Rule 6: oversize surcharge (not multiplied, not waived).
    total = base
    if max(length, width, height) > _OVERSIZE_CM:
        total += _OVERSIZE_SURCHARGE

    # Rule 7: round once, at the end.
    return total.quantize(_CENT, rounding=ROUND_HALF_UP)
