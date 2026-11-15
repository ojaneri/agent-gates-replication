from decimal import Decimal

import pytest

from solution import shipping_cost


SMALL = dict(length_cm=10, width_cm=10, height_cm=10, weight_kg=1, zone=1, subtotal=0)


def cost(**overrides):
    args = dict(SMALL)
    args.update(overrides)
    return shipping_cost(**args)


# --- Result format -------------------------------------------------------

def test_returns_decimal_with_two_places():
    result = cost()
    assert isinstance(result, Decimal)
    assert str(result) == "8.00"


# --- Base charge and billable weight ------------------------------------

@pytest.mark.parametrize(
    "weight, expected",
    [
        (0.5, "8.00"),   # billable 0.5 kg costs the first-kg rate
        (1, "8.00"),
        (1.2, "9.50"),   # rounds up to 1.5 kg
        (1.5, "9.50"),
        (1.6, "11.00"),  # rounds up to 2 kg
        (2, "11.00"),
        (3, "14.00"),
        (10, "35.00"),   # 8 + 1.5 * 18
    ],
)
def test_base_charge_by_actual_weight(weight, expected):
    assert str(cost(weight_kg=weight)) == expected


def test_volumetric_weight_can_dominate():
    # 40*40*40 / 5000 = 12.8 kg volumetric -> rounds up to 13.0 kg
    # base = 8 + 1.5 * (26 - 2) = 44.00
    result = cost(length_cm=40, width_cm=40, height_cm=40, weight_kg=1)
    assert str(result) == "44.00"


def test_actual_weight_dominates_when_heavier_than_volume():
    # volumetric = 1*1*1/5000 tiny; actual 5 kg -> 5.0 kg -> 8 + 1.5*8 = 20.00
    result = cost(length_cm=1, width_cm=1, height_cm=1, weight_kg=5)
    assert str(result) == "20.00"


def test_volumetric_exact_multiple_is_not_rounded_further():
    # 50*50*40 / 5000 = 20 kg exactly -> base = 8 + 1.5*38 = 65.00
    result = cost(length_cm=50, width_cm=50, height_cm=40, weight_kg=1)
    assert str(result) == "65.00"


def test_weight_exact_half_step_stays():
    # 2.5 kg is already a multiple of 0.5 -> 8 + 1.5*3 = 12.50
    assert str(cost(weight_kg=2.5)) == "12.50"


# --- Zone factors --------------------------------------------------------

@pytest.mark.parametrize(
    "zone, expected",
    [(1, "8.00"), (2, "10.00"), (3, "12.80")],
)
def test_zone_factor(zone, expected):
    assert str(cost(zone=zone)) == expected


def test_zone_factor_rounds_half_up_at_end():
    # 9.50 * 1.25 = 11.875 -> 11.88
    assert str(cost(weight_kg=1.5, zone=2)) == "11.88"
    # 15.625 -> 15.63
    assert str(cost(weight_kg=2.5, zone=2)) == "15.63"


def test_zone_3_no_rounding_needed():
    # 9.50 * 1.6 = 15.20
    assert str(cost(weight_kg=1.5, zone=3)) == "15.20"


# --- Free shipping -------------------------------------------------------

@pytest.mark.parametrize("zone", [1, 2])
def test_free_shipping_zone_1_and_2_at_threshold(zone):
    assert str(cost(zone=zone, subtotal=150)) == "0.00"


@pytest.mark.parametrize("zone", [1, 2])
def test_free_shipping_zone_1_and_2_above_threshold(zone):
    assert str(cost(zone=zone, subtotal=500)) == "0.00"


@pytest.mark.parametrize("zone", [1, 2])
def test_no_free_shipping_just_below_threshold(zone):
    assert cost(zone=zone, subtotal=149.99) > Decimal("0")


def test_no_free_shipping_in_zone_3():
    assert str(cost(zone=3, subtotal=1000)) == "12.80"


def test_free_shipping_keeps_oversize_surcharge():
    result = cost(length_cm=121, subtotal=200, zone=1)
    assert str(result) == "12.00"


# --- Oversize surcharge --------------------------------------------------

# Width and height are 1 cm in these tests so volumetric weight stays tiny
# and the base charge is always 8.00 in zone 1.

def test_oversize_not_triggered_at_120():
    assert str(cost(length_cm=120, width_cm=1, height_cm=1)) == "8.00"


def test_oversize_triggered_above_120():
    assert str(cost(length_cm=120.01, width_cm=1, height_cm=1)) == "20.00"


@pytest.mark.parametrize("side", ["length_cm", "width_cm", "height_cm"])
def test_oversize_checks_every_side(side):
    dims = dict(length_cm=1, width_cm=1, height_cm=1)
    dims[side] = 130
    assert str(cost(**dims)) == "20.00"


def test_oversize_surcharge_not_multiplied_by_zone_factor():
    # 8 * 1.6 = 12.80 base, plus 12.00 surcharge unmultiplied
    result = cost(length_cm=130, width_cm=1, height_cm=1, zone=3)
    assert str(result) == "24.80"


# --- Numeric input types -------------------------------------------------

def test_float_converted_through_str():
    # 0.1 kg must be exact; with a billable weight of 0.1 it rounds to 0.5 kg
    assert str(cost(weight_kg=0.1)) == "8.00"
    # 1.1 -> exactly 1.1 -> rounds up to 1.5 kg -> 9.50
    assert str(cost(weight_kg=1.1)) == "9.50"


def test_decimal_inputs_accepted():
    result = cost(weight_kg=Decimal("1.5"), subtotal=Decimal("0"))
    assert str(result) == "9.50"


@pytest.mark.parametrize("bad", ["1", None, [1], (1,), object()])
def test_non_number_raises_type_error(bad):
    with pytest.raises(TypeError):
        cost(weight_kg=bad)


@pytest.mark.parametrize("arg", ["length_cm", "width_cm", "height_cm", "weight_kg", "subtotal"])
def test_bool_is_not_a_number(arg):
    with pytest.raises(TypeError):
        cost(**{arg: True})


@pytest.mark.parametrize("arg", ["length_cm", "weight_kg", "subtotal"])
def test_nan_and_infinity_rejected(arg):
    with pytest.raises(ValueError):
        cost(**{arg: float("nan")})
    with pytest.raises(ValueError):
        cost(**{arg: Decimal("Infinity")})


# --- Value checks --------------------------------------------------------

@pytest.mark.parametrize("arg", ["length_cm", "width_cm", "height_cm", "weight_kg"])
@pytest.mark.parametrize("value", [0, -1, 0.0])
def test_dimensions_and_weight_must_be_positive(arg, value):
    with pytest.raises(ValueError):
        cost(**{arg: value})


def test_negative_subtotal_rejected():
    with pytest.raises(ValueError):
        cost(subtotal=-0.01)


def test_zero_subtotal_allowed():
    assert str(cost(subtotal=0)) == "8.00"


@pytest.mark.parametrize("zone", [True, False, 1.0, 2.0, "1", 0, 4, -1, None])
def test_invalid_zone_rejected(zone):
    with pytest.raises(ValueError):
        cost(zone=zone)


@pytest.mark.parametrize("zone", [1, 2, 3])
def test_valid_zones_accepted(zone):
    assert isinstance(cost(zone=zone), Decimal)
