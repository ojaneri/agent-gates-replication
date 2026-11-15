from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING

_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}


def _num(x):
    if isinstance(x, bool):
        raise TypeError("bool is not a number")
    if isinstance(x, Decimal):
        return x
    if isinstance(x, int):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(str(x))
    raise TypeError("not a number")


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    l, w, h, wt, sub = (_num(v) for v in (length_cm, width_cm, height_cm, weight_kg, subtotal))
    if any(not v.is_finite() for v in (l, w, h, wt, sub)):
        raise ValueError("non-finite number")
    if l <= 0 or w <= 0 or h <= 0 or wt <= 0 or sub < 0:
        raise ValueError("out of range")
    if type(zone) is not int or zone not in _FACTORS:
        raise ValueError("invalid zone")

    vol = l * w * h / Decimal(5000)
    raw = max(wt, vol)
    units = (raw * 2).to_integral_value(rounding=ROUND_CEILING)  # half-kg units
    extra = max(Decimal(0), units - 2)
    base = (Decimal(8) + Decimal("1.5") * extra) * _FACTORS[zone]
    if sub >= 150 and zone in (1, 2):
        base = Decimal(0)
    total = base
    if max(l, w, h) > 120:
        total += Decimal(12)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
