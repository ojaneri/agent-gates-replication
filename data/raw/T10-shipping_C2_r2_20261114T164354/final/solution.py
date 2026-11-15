from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, localcontext

_ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
_VOLUME_DIVISOR = Decimal("5000")
_HALF_KG = Decimal("0.5")
_FIRST_KG_CHARGE = Decimal("8.00")
_STEP_CHARGE = Decimal("1.50")
_FREE_SHIPPING_MIN_SUBTOTAL = Decimal("150")
_FREE_SHIPPING_ZONES = (1, 2)
_OVERSIZE_LIMIT_CM = Decimal("120")
_OVERSIZE_CHARGE = Decimal("12.00")
_CENT = Decimal("0.01")


def _to_decimal(value, name):
    """Convert a bool-free int, float or Decimal to a finite Decimal."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{name} must be a number")
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, float):
        number = Decimal(str(value))
    else:
        number = Decimal(value)
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


def _zone_code(zone):
    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be 1, 2 or 3")
    return zone


def _billable_weight(actual, length, width, height):
    volumetric = length * width * height / _VOLUME_DIVISOR
    heavier = max(actual, volumetric)
    halves = (heavier / _HALF_KG).to_integral_value(rounding=ROUND_CEILING)
    return halves * _HALF_KG


def _base_charge(billable):
    extra_steps = max(Decimal(0), (billable - 1) / _HALF_KG)
    return _FIRST_KG_CHARGE + _STEP_CHARGE * extra_steps


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    with localcontext() as ctx:
        ctx.prec = 60
        length = _positive(length_cm, "length_cm")
        width = _positive(width_cm, "width_cm")
        height = _positive(height_cm, "height_cm")
        weight = _positive(weight_kg, "weight_kg")
        order_value = _non_negative(subtotal, "subtotal")
        zone_number = _zone_code(zone)

        billable = _billable_weight(weight, length, width, height)
        charge = _base_charge(billable) * _ZONE_FACTORS[zone_number]
        if order_value >= _FREE_SHIPPING_MIN_SUBTOTAL and zone_number in _FREE_SHIPPING_ZONES:
            charge = Decimal(0)
        if max(length, width, height) > _OVERSIZE_LIMIT_CM:
            charge += _OVERSIZE_CHARGE
        return charge.quantize(_CENT, rounding=ROUND_HALF_UP)
