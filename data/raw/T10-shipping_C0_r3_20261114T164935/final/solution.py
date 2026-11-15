import math
from decimal import Decimal
from fractions import Fraction

_ZONE_FACTORS = {1: Fraction(1), 2: Fraction(5, 4), 3: Fraction(8, 5)}
_BASE_FIRST_KG = Fraction(8)
_PER_HALF_KG = Fraction(3, 2)  # 1.50 per further 0.5 kg
_VOLUME_DIVISOR = 5000
_OVERSIZE_CM = 120
_OVERSIZE_SURCHARGE = Fraction(12)
_FREE_SHIPPING_SUBTOTAL = Fraction(150)


def _to_fraction(value, name: str) -> Fraction:
    """Convert a number to an exact Fraction, following the spec's rules."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        dec = Decimal(str(value))  # exact decimal meaning of the float's str()
    elif isinstance(value, Decimal):
        dec = value
    else:
        raise TypeError(f"{name} must be an int, float or Decimal")
    if not dec.is_finite():
        raise ValueError(f"{name} must be a finite number")
    return Fraction(dec)


def _positive(value, name: str) -> Fraction:
    number = _to_fraction(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def _non_negative(value, name: str) -> Fraction:
    number = _to_fraction(value, name)
    if number < 0:
        raise ValueError(f"{name} must be zero or more")
    return number


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _positive(length_cm, "length_cm")
    width = _positive(width_cm, "width_cm")
    height = _positive(height_cm, "height_cm")
    weight = _positive(weight_kg, "weight_kg")
    subtotal_value = _non_negative(subtotal, "subtotal")

    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be the int 1, 2 or 3")
    factor = _ZONE_FACTORS[zone]

    # Rules 1-2: billable weight, rounded up to the next multiple of 0.5 kg.
    volumetric = length * width * height / _VOLUME_DIVISOR
    billable = max(weight, volumetric)
    half_kg_units = math.ceil(billable * 2)

    # Rule 3: base charge.
    if half_kg_units <= 2:
        base = _BASE_FIRST_KG
    else:
        base = _BASE_FIRST_KG + _PER_HALF_KG * (half_kg_units - 2)

    # Rules 4-5: zone factor, then free shipping for zones 1 and 2.
    if subtotal_value >= _FREE_SHIPPING_SUBTOTAL and zone in (1, 2):
        charge = Fraction(0)
    else:
        charge = base * factor

    # Rule 6: oversize surcharge, not multiplied and not waived.
    if max(length, width, height) > _OVERSIZE_CM:
        charge += _OVERSIZE_SURCHARGE

    # Rule 7: round half up to cents, only at the end. The charge is never negative.
    cents = math.floor(charge * 100 + Fraction(1, 2))
    return Decimal(f"{cents // 100}.{cents % 100:02d}")
