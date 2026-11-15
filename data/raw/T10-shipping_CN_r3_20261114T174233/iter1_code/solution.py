import math
from decimal import Decimal, ROUND_HALF_UP


def _to_decimal(value) -> Decimal:
    """Convert an int, float or Decimal to Decimal; reject everything else."""
    if isinstance(value, bool):
        raise TypeError("bool is not a valid number")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        result = Decimal(str(value))
    else:
        raise TypeError(f"expected int, float or Decimal, got {type(value).__name__}")
    if not result.is_finite():
        raise ValueError("number must be finite")
    return result


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm)
    width = _to_decimal(width_cm)
    height = _to_decimal(height_cm)
    weight = _to_decimal(weight_kg)
    order_subtotal = _to_decimal(subtotal)

    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("dimensions must be greater than zero")
    if weight <= 0:
        raise ValueError("weight must be greater than zero")
    if order_subtotal < 0:
        raise ValueError("subtotal must be zero or more")

    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in (1, 2, 3):
        raise ValueError("zone must be the int 1, 2 or 3")

    # Rule 1: volumetric weight.
    volumetric = length * width * height / Decimal(5000)

    # Rule 2: billable weight, rounded up to the next multiple of 0.5 kg.
    # Work in half-kilogram units to keep the rounding exact.
    raw_billable = max(weight, volumetric)
    half_units = math.ceil(raw_billable * 2)  # number of 0.5 kg steps (>= 1)

    # Rule 3: 8.00 for the first kilogram (2 half-units), then 1.50 per further 0.5 kg.
    extra_steps = max(0, half_units - 2)
    base = Decimal("8.00") + Decimal("1.50") * extra_steps

    # Rule 4: zone factor.
    zone_factor = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}[zone]
    base = base * zone_factor

    # Rule 5: free shipping for subtotal >= 150 in zones 1 and 2.
    if order_subtotal >= 150 and zone in (1, 2):
        base = Decimal(0)

    # Rule 6: oversize surcharge, not multiplied and not waived.
    total = base
    if max(length, width, height) > 120:
        total += Decimal("12.00")

    # Rule 7: round once, at the end.
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
