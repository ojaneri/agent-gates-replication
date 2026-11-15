from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

VOL_DIVISOR = Decimal("5000")
FIRST_KG = Decimal("8.00")
STEP = Decimal("0.5")
STEP_PRICE = Decimal("1.50")
ZONE_FACTOR = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
FREE_FROM = Decimal("150")
FREE_ZONES = (1, 2)
OVERSIZE_SIDE = Decimal("120")
OVERSIZE_FEE = Decimal("12.00")
CENT = Decimal("0.01")


def _num(x, name: str) -> Decimal:
    if isinstance(x, bool) or not isinstance(x, (int, float, Decimal)):
        raise TypeError(f"{name} must be a number")
    d = Decimal(str(x))
    if d.is_nan():
        raise ValueError(f"{name} must not be NaN")
    return d


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    dims = [_num(length_cm, "length_cm"), _num(width_cm, "width_cm"), _num(height_cm, "height_cm")]
    weight = _num(weight_kg, "weight_kg")
    sub = _num(subtotal, "subtotal")
    if any(d <= 0 for d in dims) or weight <= 0:
        raise ValueError("dimensions and weight must be positive")
    if sub < 0:
        raise ValueError("subtotal must not be negative")
    if type(zone) is not int or zone not in ZONE_FACTOR:
        raise ValueError("zone must be 1, 2 or 3")
    length, width, height = dims
    volumetric = length * width * height / VOL_DIVISOR
    billable = max(volumetric, weight)
    billable = (billable / STEP).to_integral_value(rounding=ROUND_CEILING) * STEP
    base = FIRST_KG + max(billable - 1, 0) / STEP * STEP_PRICE
    base = base * ZONE_FACTOR[zone]
    if sub >= FREE_FROM and zone in FREE_ZONES:
        base = Decimal(0)
    fee = OVERSIZE_FEE if max(dims) > OVERSIZE_SIDE else Decimal(0)
    return (base + fee).quantize(CENT, rounding=ROUND_HALF_UP)
