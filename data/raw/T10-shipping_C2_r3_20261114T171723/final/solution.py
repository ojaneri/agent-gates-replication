from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
FREE_SHIPPING_ZONES = (1, 2)
FIRST_KG_CHARGE = Decimal("8.00")
EXTRA_HALF_KG_CHARGE = Decimal("1.50")
VOLUMETRIC_DIVISOR = Decimal("5000")
FREE_SHIPPING_SUBTOTAL = Decimal("150")
OVERSIZE_LIMIT_CM = Decimal("120")
OVERSIZE_SURCHARGE = Decimal("12.00")
CENT = Decimal("0.01")


def _to_decimal(value, name):
    """Convert a number to Decimal, rejecting bool, non-numbers and non-finite values."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, float):
        number = Decimal(str(value))
    else:
        raise TypeError(f"{name} must be a number, not {type(value).__name__}")
    if not number.is_finite():
        raise ValueError(f"{name} must be finite")
    return number


def _positive(value, name):
    number = _to_decimal(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def _non_negative(value, name):
    number = _to_decimal(value, name)
    if number < 0:
        raise ValueError(f"{name} must be zero or more")
    return number


def _validate_zone(zone):
    if type(zone) is not int or zone not in ZONE_FACTORS:
        raise ValueError("zone must be the int 1, 2 or 3")


def _billable_weight(actual_kg, volumetric_kg):
    """Heavier of actual and volumetric weight, rounded up to a multiple of 0.5 kg."""
    heavier = max(actual_kg, volumetric_kg)
    half_kg_units = (heavier * 2).to_integral_value(rounding=ROUND_CEILING)
    return half_kg_units / 2


def _base_charge(billable_kg):
    if billable_kg <= 1:
        return FIRST_KG_CHARGE
    extra_half_kgs = (billable_kg - 1) * 2
    return FIRST_KG_CHARGE + EXTRA_HALF_KG_CHARGE * extra_half_kgs


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _positive(length_cm, "length_cm")
    width = _positive(width_cm, "width_cm")
    height = _positive(height_cm, "height_cm")
    weight = _positive(weight_kg, "weight_kg")
    cart_total = _non_negative(subtotal, "subtotal")
    _validate_zone(zone)

    volumetric = length * width * height / VOLUMETRIC_DIVISOR
    billable = _billable_weight(weight, volumetric)
    base = _base_charge(billable) * ZONE_FACTORS[zone]
    if cart_total >= FREE_SHIPPING_SUBTOTAL and zone in FREE_SHIPPING_ZONES:
        base = Decimal(0)

    surcharge = Decimal(0)
    if max(length, width, height) > OVERSIZE_LIMIT_CM:
        surcharge = OVERSIZE_SURCHARGE

    return (base + surcharge).quantize(CENT, rounding=ROUND_HALF_UP)
