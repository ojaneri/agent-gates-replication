from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP


_CENT = Decimal("0.01")
_HALF_KG = Decimal("0.5")
_ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}


def _to_decimal(value, name):
    """Convert a number (int, float or Decimal, not bool) to Decimal exactly."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        result = Decimal(str(value))
    else:
        raise TypeError(f"{name} must be int, float or Decimal")
    if not result.is_finite():
        raise ValueError(f"{name} must be a finite number")
    return result


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm, "length_cm")
    width = _to_decimal(width_cm, "width_cm")
    height = _to_decimal(height_cm, "height_cm")
    weight = _to_decimal(weight_kg, "weight_kg")
    sub = _to_decimal(subtotal, "subtotal")

    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("dimensions must be greater than zero")
    if weight <= 0:
        raise ValueError("weight_kg must be greater than zero")
    if sub < 0:
        raise ValueError("subtotal must be zero or more")

    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be the int 1, 2 or 3")

    # Rule 1: volumetric weight; Rule 2: larger of actual and volumetric,
    # rounded up to the next multiple of 0.5 kg.
    volumetric = length * width * height / Decimal(5000)
    raw_billable = max(weight, volumetric)
    halves = (raw_billable / _HALF_KG).to_integral_value(rounding=ROUND_CEILING)
    billable = halves * _HALF_KG

    # Rule 3: 8.00 for the first kg, plus 1.50 per further 0.5 kg.
    if billable <= 1:
        base = Decimal("8.00")
    else:
        extra_steps = (billable - 1) / _HALF_KG  # whole number, since billable is a multiple of 0.5
        base = Decimal("8.00") + Decimal("1.50") * extra_steps

    # Rule 4: zone factor.
    base = base * _ZONE_FACTORS[zone]

    # Rule 5: free shipping for subtotal >= 150 in zones 1 and 2.
    if sub >= 150 and zone in (1, 2):
        base = Decimal("0")

    # Rule 6: oversize surcharge, not multiplied and not waived.
    total = base
    if max(length, width, height) > 120:
        total += Decimal("12.00")

    # Rule 7: round once, at the end.
    return total.quantize(_CENT, rounding=ROUND_HALF_UP)
