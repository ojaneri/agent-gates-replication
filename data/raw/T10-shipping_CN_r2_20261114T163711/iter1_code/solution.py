from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

_ZONE_FACTORS = {
    1: Decimal("1"),
    2: Decimal("1.25"),
    3: Decimal("1.6"),
}


def _to_decimal(value, name):
    """Convert a number (int, float or Decimal) to Decimal; reject anything else."""
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
    subtotal_d = _to_decimal(subtotal, "subtotal")

    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("dimensions must be greater than zero")
    if weight <= 0:
        raise ValueError("weight_kg must be greater than zero")
    if subtotal_d < 0:
        raise ValueError("subtotal must be zero or more")

    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be the int 1, 2 or 3")

    # Rule 1: volumetric weight.
    volumetric = length * width * height / Decimal("5000")

    # Rule 2: billable weight, rounded up to the next multiple of 0.5 kg.
    raw_billable = max(weight, volumetric)
    half_steps = (raw_billable * 2).to_integral_value(rounding=ROUND_CEILING)
    billable = half_steps / Decimal("2")

    # Rule 3: base charge.
    if billable <= 1:
        base = Decimal("8.00")
    else:
        base = Decimal("8.00") + Decimal("1.50") * (billable - 1) / Decimal("0.5")

    # Rule 4: zone factor.
    base = base * _ZONE_FACTORS[zone]

    # Rule 5: free shipping for zones 1 and 2 on large subtotals.
    if subtotal_d >= 150 and zone in (1, 2):
        base = Decimal("0")

    # Rule 6: oversize surcharge (not multiplied, not waived).
    total = base
    if max(length, width, height) > 120:
        total += Decimal("12.00")

    # Rule 7: round at the end.
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
