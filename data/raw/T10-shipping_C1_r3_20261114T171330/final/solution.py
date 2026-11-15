from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

_ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
_VOLUME_DIVISOR = Decimal("5000")
_FIRST_KG_CHARGE = Decimal("8.00")
_EXTRA_HALF_KG_CHARGE = Decimal("1.50")
_FREE_SHIPPING_SUBTOTAL = Decimal("150")
_FREE_SHIPPING_ZONES = (1, 2)
_OVERSIZE_SIDE_CM = Decimal("120")
_OVERSIZE_SURCHARGE = Decimal("12.00")
_CENT = Decimal("0.01")


def _to_decimal(value, name):
    """Convert a number argument to a finite Decimal, or raise."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        result = Decimal(str(value))
    else:
        raise TypeError(f"{name} must be int, float or Decimal, not {type(value).__name__}")
    if not result.is_finite():
        raise ValueError(f"{name} must be a finite number")
    return result


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm, "length_cm")
    width = _to_decimal(width_cm, "width_cm")
    height = _to_decimal(height_cm, "height_cm")
    weight = _to_decimal(weight_kg, "weight_kg")
    order_subtotal = _to_decimal(subtotal, "subtotal")

    if type(zone) is not int or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be the int 1, 2 or 3")

    if min(length, width, height, weight) <= 0:
        raise ValueError("dimensions and weight must be greater than zero")
    if order_subtotal < 0:
        raise ValueError("subtotal must be zero or more")

    # Rule 1 and 2: billable weight, rounded up to the next 0.5 kg step.
    volumetric = length * width * height / _VOLUME_DIVISOR
    billable = max(weight, volumetric)
    half_kg_steps = (billable * 2).to_integral_value(rounding=ROUND_CEILING)

    # Rule 3: 8.00 for the first kg, then 1.50 per further 0.5 kg.
    extra_steps = max(Decimal(0), half_kg_steps - 2)
    base = _FIRST_KG_CHARGE + _EXTRA_HALF_KG_CHARGE * extra_steps

    # Rule 4: zone factor.
    base = base * _ZONE_FACTORS[zone]

    # Rule 5: free shipping waives the base charge only.
    if order_subtotal >= _FREE_SHIPPING_SUBTOTAL and zone in _FREE_SHIPPING_ZONES:
        base = Decimal(0)

    # Rule 6: oversize surcharge, added after the zone factor and free shipping.
    total = base
    if max(length, width, height) > _OVERSIZE_SIDE_CM:
        total += _OVERSIZE_SURCHARGE

    # Rule 7: round only at the end.
    return total.quantize(_CENT, rounding=ROUND_HALF_UP)
