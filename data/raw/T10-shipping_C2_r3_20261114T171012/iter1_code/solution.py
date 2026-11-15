from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}


def _to_decimal(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError("number expected")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("value must be finite")
    return result


def _billable_half_kgs(dims, weight) -> Decimal:
    volumetric = dims[0] * dims[1] * dims[2] / Decimal(5000)
    heavier = max(weight, volumetric)
    return (heavier * 2).to_integral_value(rounding=ROUND_CEILING)


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    dims = [_to_decimal(v) for v in (length_cm, width_cm, height_cm)]
    weight = _to_decimal(weight_kg)
    money = _to_decimal(subtotal)
    if min(dims) <= 0 or weight <= 0 or money < 0:
        raise ValueError("invalid measurement")
    if type(zone) is not int or zone not in _FACTORS:
        raise ValueError("zone must be 1, 2 or 3")

    half_kgs = _billable_half_kgs(dims, weight)
    base = Decimal(8) + Decimal("1.5") * max(Decimal(0), half_kgs - 2)
    base *= _FACTORS[zone]
    if money >= 150 and zone in (1, 2):
        base = Decimal(0)
    total = base
    if max(dims) > 120:
        total += Decimal(12)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
