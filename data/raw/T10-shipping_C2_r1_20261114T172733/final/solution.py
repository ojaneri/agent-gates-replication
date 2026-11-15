from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}


def _to_decimal(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError("numeric value required")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("value must be finite")
    return result


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm)
    width = _to_decimal(width_cm)
    height = _to_decimal(height_cm)
    weight = _to_decimal(weight_kg)
    amount = _to_decimal(subtotal)
    if min(length, width, height, weight) <= 0 or amount < 0:
        raise ValueError("invalid dimensions, weight or subtotal")
    if type(zone) is not int or zone not in ZONE_FACTORS:
        raise ValueError("zone must be 1, 2 or 3")

    volumetric = length * width * height / 5000
    half_kgs = (max(weight, volumetric) * 2).to_integral_value(ROUND_CEILING)
    base = (Decimal(8) + Decimal("1.5") * max(Decimal(0), half_kgs - 2)) * ZONE_FACTORS[zone]
    if amount >= 150 and zone in (1, 2):
        base = Decimal(0)
    total = base
    if max(length, width, height) > 120:
        total += Decimal(12)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
