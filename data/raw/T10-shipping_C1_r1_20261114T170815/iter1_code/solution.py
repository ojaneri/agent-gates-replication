from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

_ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
_VOLUME_DIVISOR = Decimal("5000")
_BASE_FIRST_KG = Decimal("8.00")
_PER_HALF_KG = Decimal("1.50")
_FREE_SHIPPING_SUBTOTAL = Decimal("150")
_FREE_SHIPPING_ZONES = (1, 2)
_OVERSIZE_CM = Decimal("120")
_OVERSIZE_SURCHARGE = Decimal("12.00")
_CENT = Decimal("0.01")


def _to_decimal(value, name):
    """Convert a number (int, float or Decimal, not bool) to a finite Decimal."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, float):
        number = Decimal(str(value))
    else:
        raise TypeError(f"{name} must be int, float or Decimal")
    if not number.is_finite():
        raise ValueError(f"{name} must be a finite number")
    return number


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm, "length_cm")
    width = _to_decimal(width_cm, "width_cm")
    height = _to_decimal(height_cm, "height_cm")
    weight = _to_decimal(weight_kg, "weight_kg")
    order_subtotal = _to_decimal(subtotal, "subtotal")

    if type(zone) is not int or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be 1, 2 or 3")

    for name, value in (("length_cm", length), ("width_cm", width),
                        ("height_cm", height), ("weight_kg", weight)):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero")
    if order_subtotal < 0:
        raise ValueError("subtotal must be zero or more")

    # Rule 1-2: billable weight = max(actual, volumetric), rounded up to 0.5 kg.
    volumetric = length * width * height / _VOLUME_DIVISOR
    heavier = max(weight, volumetric)
    billable = (heavier * 2).to_integral_value(rounding=ROUND_CEILING) / 2

    # Rule 3: 8.00 for the first kg, plus 1.50 per further 0.5 kg.
    half_kg_steps_after_first = max(billable - 1, Decimal("0")) * 2
    base = _BASE_FIRST_KG + _PER_HALF_KG * half_kg_steps_after_first

    # Rule 4: zone factor.
    charge = base * _ZONE_FACTORS[zone]

    # Rule 5: free shipping for zones 1 and 2 at a subtotal of 150 or more.
    if order_subtotal >= _FREE_SHIPPING_SUBTOTAL and zone in _FREE_SHIPPING_ZONES:
        charge = Decimal("0")

    # Rule 6: oversize surcharge, not multiplied by zone factor, not waived.
    if max(length, width, height) > _OVERSIZE_CM:
        charge += _OVERSIZE_SURCHARGE

    # Rule 7: round once, at the end, half up.
    return charge.quantize(_CENT, rounding=ROUND_HALF_UP)
