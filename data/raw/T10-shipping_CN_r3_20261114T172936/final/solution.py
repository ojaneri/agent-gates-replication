from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING


def _num(x) -> Decimal:
    if isinstance(x, bool):
        raise TypeError("bool is not a number")
    if isinstance(x, float):
        return Decimal(str(x))
    if isinstance(x, (int, Decimal)):
        return Decimal(x)
    raise TypeError("not a number")


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    l = _num(length_cm)
    w = _num(width_cm)
    h = _num(height_cm)
    kg = _num(weight_kg)
    sub = _num(subtotal)

    for v in (l, w, h, kg, sub):
        if not v.is_finite():
            raise ValueError("non-finite number")
    if l <= 0 or w <= 0 or h <= 0 or kg <= 0:
        raise ValueError("dimensions and weight must be > 0")
    if sub < 0:
        raise ValueError("subtotal must be >= 0")
    if type(zone) is not int or zone not in (1, 2, 3):
        raise ValueError("invalid zone")

    vol = l * w * h / Decimal(5000)
    billable = max(kg, vol)
    halves = (billable * 2).to_integral_value(rounding=ROUND_CEILING)
    extra = max(Decimal(0), halves - 2)
    base = Decimal("8.00") + Decimal("1.50") * extra

    factor = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}[zone]
    base *= factor
    if sub >= 150 and zone in (1, 2):
        base = Decimal(0)

    total = base
    if max(l, w, h) > 120:
        total += Decimal("12.00")
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
