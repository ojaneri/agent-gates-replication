import math
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

_ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
_VOLUME_DIVISOR = Decimal("5000")
_HALF = Decimal("0.5")
_CENT = Decimal("0.01")


def _to_number(value, name):
    """Convert an input to Decimal, rejecting bool and non-numeric types."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        result = Decimal(str(value))
    elif isinstance(value, Decimal):
        result = value
    else:
        raise TypeError(f"{name} must be an int, float or Decimal")
    if not result.is_finite():
        raise ValueError(f"{name} must be a finite number")
    return result


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_number(length_cm, "length_cm")
    width = _to_number(width_cm, "width_cm")
    height = _to_number(height_cm, "height_cm")
    weight = _to_number(weight_kg, "weight_kg")
    total_subtotal = _to_number(subtotal, "subtotal")

    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be the int 1, 2 or 3")

    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("dimensions must be greater than zero")
    if weight <= 0:
        raise ValueError("weight_kg must be greater than zero")
    if total_subtotal < 0:
        raise ValueError("subtotal must be zero or more")

    # Rule 1-2: billable weight is the larger of actual and volumetric weight,
    # rounded up to the next multiple of 0.5 kg.
    volumetric = length * width * height / _VOLUME_DIVISOR
    raw_billable = max(weight, volumetric)
    half_units = (raw_billable / _HALF).to_integral_value(rounding=ROUND_CEILING)
    billable = half_units * _HALF

    # Rule 3: 8.00 for the first kg, plus 1.50 per further 0.5 kg.
    if billable <= 1:
        base = Decimal("8.00")
    else:
        extra_steps = (billable - 1) / _HALF
        base = Decimal("8.00") + Decimal("1.50") * extra_steps

    # Rule 4: zone factor.
    base = base * _ZONE_FACTORS[zone]

    # Rule 5: free shipping for zones 1 and 2 at subtotal >= 150.
    if total_subtotal >= 150 and zone in (1, 2):
        base = Decimal("0")

    # Rule 6: oversize surcharge, not multiplied and not waived.
    surcharge = Decimal("0")
    if max(length, width, height) > 120:
        surcharge = Decimal("12.00")

    # Rule 7: round once, at the end.
    total = (base + surcharge).quantize(_CENT, rounding=ROUND_HALF_UP)
    return total
