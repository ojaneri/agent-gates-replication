from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float, Decimal)):
        raise TypeError("number required")
    d = Decimal(str(x)) if isinstance(x, float) else Decimal(x)
    return d


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    l, w, h, kg, sub = (_num(v) for v in (length_cm, width_cm, height_cm, weight_kg, subtotal))
    for v in (l, w, h, kg, sub):
        if not v.is_finite():
            raise ValueError("non-finite number")
    if l <= 0 or w <= 0 or h <= 0 or kg <= 0 or sub < 0:
        raise ValueError("out of range")
    if type(zone) is not int or zone not in (1, 2, 3):
        raise ValueError("invalid zone")

    vol = l * w * h / Decimal(5000)
    billable = (max(kg, vol) * 2).to_integral_value(rounding=ROUND_CEILING) / 2
    halves = int(billable * 2)
    base = Decimal("8.00") + Decimal("1.50") * max(0, halves - 2)
    base *= {1: Decimal(1), 2: Decimal("1.25"), 3: Decimal("1.6")}[zone]
    if sub >= 150 and zone in (1, 2):
        base = Decimal(0)
    if max(l, w, h) > 120:
        base += Decimal("12.00")
    return base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
