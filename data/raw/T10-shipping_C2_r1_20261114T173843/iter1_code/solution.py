"""Parcel shipping cost calculation. See spec.md."""
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, localcontext

_WORKING_PRECISION = 60
_TWO_PLACES = Decimal("0.01")
_VOLUME_DIVISOR = Decimal(5000)
_HALF_KG_STEP = Decimal("0.5")
_FIRST_KG_CHARGE = Decimal("8.00")
_EXTRA_HALF_KG_CHARGE = Decimal("1.50")
_OVERSIZE_LIMIT_CM = Decimal(120)
_OVERSIZE_SURCHARGE = Decimal("12.00")
_FREE_SHIPPING_SUBTOTAL = Decimal(150)
_ZONE_FACTORS = {1: Decimal(1), 2: Decimal("1.25"), 3: Decimal("1.6")}
_FREE_SHIPPING_ZONES = (1, 2)


def _to_decimal(value) -> Decimal:
    if isinstance(value, bool):
        raise TypeError("booleans are not valid numbers")
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, float):
        number = Decimal(str(value))
    else:
        raise TypeError(f"expected a number, got {type(value).__name__}")
    if not number.is_finite():
        raise ValueError("numbers must be finite")
    return number


def _require_positive(value: Decimal, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def _validate_zone(zone) -> int:
    if isinstance(zone, bool) or not isinstance(zone, int) or zone not in _ZONE_FACTORS:
        raise ValueError("zone must be 1, 2 or 3")
    return zone


def _billable_weight(length: Decimal, width: Decimal, height: Decimal, weight: Decimal) -> Decimal:
    volumetric = length * width * height / _VOLUME_DIVISOR
    heavier = max(weight, volumetric)
    half_kg_steps = (heavier / _HALF_KG_STEP).to_integral_value(rounding=ROUND_CEILING)
    return half_kg_steps * _HALF_KG_STEP


def _base_charge(billable: Decimal) -> Decimal:
    extra_half_kgs = (max(billable, Decimal(1)) - 1) / _HALF_KG_STEP
    return _FIRST_KG_CHARGE + _EXTRA_HALF_KG_CHARGE * extra_half_kgs


def _oversize_surcharge(length: Decimal, width: Decimal, height: Decimal) -> Decimal:
    if max(length, width, height) > _OVERSIZE_LIMIT_CM:
        return _OVERSIZE_SURCHARGE
    return Decimal(0)


def _is_free_shipping(zone: int, subtotal: Decimal) -> bool:
    return subtotal >= _FREE_SHIPPING_SUBTOTAL and zone in _FREE_SHIPPING_ZONES


def shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal) -> Decimal:
    """Return the shipping charge. See spec.md."""
    length = _to_decimal(length_cm)
    width = _to_decimal(width_cm)
    height = _to_decimal(height_cm)
    weight = _to_decimal(weight_kg)
    order_subtotal = _to_decimal(subtotal)
    for name, value in (
        ("length_cm", length),
        ("width_cm", width),
        ("height_cm", height),
        ("weight_kg", weight),
    ):
        _require_positive(value, name)
    if order_subtotal < 0:
        raise ValueError("subtotal must be zero or more")
    zone = _validate_zone(zone)
    with localcontext() as ctx:
        ctx.prec = _WORKING_PRECISION
        base = _base_charge(_billable_weight(length, width, height, weight))
        if _is_free_shipping(zone, order_subtotal):
            base = Decimal(0)
        total = base * _ZONE_FACTORS[zone] + _oversize_surcharge(length, width, height)
        return total.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
