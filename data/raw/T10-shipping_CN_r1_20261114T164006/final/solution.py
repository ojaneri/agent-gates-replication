from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING


def _num(x) -> Decimal:
    if isinstance(x, bool) or not isinstance(x, (int, float, Decimal)):
        raise TypeError("numeric value required")
    d = Decimal(str(x)) if isinstance(x, float) else Decimal(x)
    if not d.is_finite():
        raise ValueError("value must be finite")
    return d


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    l = _num(length_cm)
    w = _num(width_cm)
    h = _num(height_cm)
    kg = _num(weight_kg)
    sub = _num(subtotal)
    if l <= 0 or w <= 0 or h <= 0 or kg <= 0 or sub < 0:
        raise ValueError("invalid value")
    if type(zone) is not int or zone not in (1, 2, 3):
        raise ValueError("invalid zone")

    vol = l * w * h / Decimal(5000)
    billable = max(kg, vol)
    units = (billable / Decimal("0.5")).to_integral_value(rounding=ROUND_CEILING)
    base = Decimal(8) + Decimal("1.5") * max(Decimal(0), units - 2)
    factor = {1: Decimal(1), 2: Decimal("1.25"), 3: Decimal("1.6")}[zone]
    base *= factor
    if sub >= 150 and zone in (1, 2):
        base = Decimal(0)
    total = base
    if max(l, w, h) > 120:
        total += Decimal(12)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
