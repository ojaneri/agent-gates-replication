from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, localcontext

_ZONE_FACTORS = {1: Decimal("1"), 2: Decimal("1.25"), 3: Decimal("1.6")}
_FREE_SHIPPING_ZONES = (1, 2)
_FREE_SHIPPING_MIN_SUBTOTAL = Decimal("150")
_VOLUME_DIVISOR = Decimal("5000")
_ONE = Decimal("1")
_HALF = Decimal("0.5")
_BASE_FIRST_KG = Decimal("8.00")
_BASE_PER_HALF_KG = Decimal("1.50")
_OVERSIZE_LENGTH = Decimal("120")
_OVERSIZE_SURCHARGE = Decimal("12.00")
_CENT = Decimal("0.01")


def _to_decimal(value, name: str) -> Decimal:
    """Convert a numeric input to Decimal, rejecting bool and non-numbers."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be int, float or Decimal, not bool")
    if isinstance(value, float):
        number = Decimal(str(value))
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, Decimal):
        number = value
    else:
        raise TypeError(f"{name} must be int, float or Decimal")
    if not number.is_finite():
        raise ValueError(f"{name} must be a finite number")
    return number


def _round_up_to_half_kg(weight: Decimal) -> Decimal:
    """Round up to the next multiple of 0.5 (multiples stay unchanged)."""
    return (weight * 2).to_integral_value(rounding=ROUND_CEILING) / 2


def _base_charge(billable: Decimal) -> Decimal:
    """8.00 for the first kg, plus 1.50 per further 0.5 kg."""
    if billable <= _ONE:
        return _BASE_FIRST_KG
    extra_steps = int((billable - _ONE) / _HALF)
    return _BASE_FIRST_KG + _BASE_PER_HALF_KG * extra_steps


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm, "length_cm")
    width = _to_decimal(width_cm, "width_cm")
    height = _to_decimal(height_cm, "height_cm")
    weight = _to_decimal(weight_kg, "weight_kg")
    order_subtotal = _to_decimal(subtotal, "subtotal")

    for name, value in (("length_cm", length), ("width_cm", width),
                        ("height_cm", height), ("weight_kg", weight)):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero")
    if order_subtotal < 0:
        raise ValueError("subtotal must be zero or more")
    if type(zone) is not int or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be 1, 2 or 3")

    with localcontext() as ctx:
        ctx.prec = 100

        volumetric = length * width * height / _VOLUME_DIVISOR
        billable = _round_up_to_half_kg(max(weight, volumetric))
        base = _base_charge(billable)

        if order_subtotal >= _FREE_SHIPPING_MIN_SUBTOTAL and zone in _FREE_SHIPPING_ZONES:
            charge = Decimal("0")
        else:
            charge = base * _ZONE_FACTORS[zone]

        if max(length, width, height) > _OVERSIZE_LENGTH:
            charge += _OVERSIZE_SURCHARGE

        return charge.quantize(_CENT, rounding=ROUND_HALF_UP)
