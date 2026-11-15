from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING


def _to_dec(x):
    if isinstance(x, bool) or not isinstance(x, (int, float, Decimal)):
        raise TypeError("number expected")
    d = Decimal(str(x)) if isinstance(x, float) else Decimal(x)
    if not d.is_finite():
        raise ValueError("finite number expected")
    return d


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    l = _to_dec(length_cm)
    w = _to_dec(width_cm)
    h = _to_dec(height_cm)
    wt = _to_dec(weight_kg)
    sub = _to_dec(subtotal)
    if l <= 0 or w <= 0 or h <= 0 or wt <= 0 or sub < 0:
        raise ValueError("invalid value")
    if type(zone) is not int or zone not in (1, 2, 3):
        raise ValueError("invalid zone")

    vol = l * w * h / Decimal(5000)
    billable = max(wt, vol)
    units = (billable / Decimal("0.5")).to_integral_value(rounding=ROUND_CEILING)
    base = Decimal(8) + Decimal("1.5") * max(units - 2, 0)
    base *= {1: Decimal(1), 2: Decimal("1.25"), 3: Decimal("1.6")}[zone]
    if sub >= 150 and zone in (1, 2):
        base = Decimal(0)
    total = base
    if max(l, w, h) > 120:
        total += Decimal(12)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
