from decimal import Decimal

import pytest

from solution import shipping_cost


SMALL = dict(length_cm=10, width_cm=10, height_cm=10)


def cost(weight=1, zone=1, subtotal=0, **dims):
    d = dict(SMALL)
    d.update(dims)
    return shipping_cost(d["length_cm"], d["width_cm"], d["height_cm"], weight, zone, subtotal)


# ---- billable weight and base charge ----

@pytest.mark.parametrize(
    "weight, expected",
    [
        (Decimal("0.5"), "8.00"),
        (1, "8.00"),
        (Decimal("1.5"), "9.50"),
        (2, "11.00"),
        (1.2, "9.50"),      # rounds up to 1.5
        (2.1, "12.50"),     # rounds up to 2.5
        (1.0000001, "9.50"),  # any excess over 1 kg bills the next half kg
        (0.1, "8.00"),
    ],
)
def test_base_charge_by_weight_zone1(weight, expected):
    result = cost(weight=weight)
    assert result == Decimal(expected)


def test_result_type_and_two_places():
    result = cost(weight=1)
    assert isinstance(result, Decimal)
    assert str(result) == "8.00"


def test_float_is_converted_through_str():
    # 1.5 as float is exact; check float input path gives the same as Decimal.
    assert cost(weight=1.5) == cost(weight=Decimal("1.5")) == Decimal("9.50")


def test_decimal_inputs_are_accepted():
    result = shipping_cost(Decimal("10"), Decimal("10"), Decimal("10"),
                           Decimal("2"), 1, Decimal("0"))
    assert result == Decimal("11.00")


def test_integer_inputs_are_accepted():
    assert shipping_cost(10, 10, 10, 2, 1, 0) == Decimal("11.00")


# ---- volumetric weight ----

def test_volumetric_weight_wins_over_actual():
    # 50*50*20 / 5000 = 10 kg; actual 1 kg -> billable 10 -> 8 + 3*9 = 35
    assert cost(weight=1, length_cm=50, width_cm=50, height_cm=20) == Decimal("35.00")


def test_actual_weight_wins_over_volumetric():
    # volumetric 0.2 kg; actual 2 kg -> 11.00
    assert cost(weight=2) == Decimal("11.00")


def test_large_volumetric_weight():
    # 100*100*100 / 5000 = 200 kg -> 8 + 3*199 = 605
    assert cost(weight=1, length_cm=100, width_cm=100, height_cm=100) == Decimal("605.00")


def test_volumetric_rounded_up_to_half_kg():
    # 10*10*11 / 5000 = 0.22 kg -> rounds to 0.5 -> 8.00
    assert cost(weight=0.1, height_cm=11) == Decimal("8.00")
    # 10*10*105 / 5000 = 2.1 kg -> rounds to 2.5 -> 12.50
    assert cost(weight=0.1, height_cm=105) == Decimal("12.50")


# ---- zone factors ----

@pytest.mark.parametrize(
    "zone, weight, expected",
    [
        (1, 1.5, "9.50"),
        (2, 1.5, "11.88"),    # 9.5 * 1.25 = 11.875 -> half up
        (3, 1.5, "15.20"),    # 9.5 * 1.6
        (3, 2, "17.60"),      # 11 * 1.6
        (2, 2, "13.75"),      # 11 * 1.25
    ],
)
def test_zone_factors(zone, weight, expected):
    assert cost(weight=weight, zone=zone) == Decimal(expected)


def test_rounding_is_half_up_not_bankers():
    # 12.50 * 1.25 = 15.625 -> ROUND_HALF_UP gives 15.63 (bankers would give 15.62)
    assert cost(weight=2.5, zone=2) == Decimal("15.63")


# ---- free shipping ----

def test_free_shipping_zone1_at_threshold():
    assert cost(weight=2, zone=1, subtotal=150) == Decimal("0.00")


def test_free_shipping_zone2_above_threshold():
    assert cost(weight=2, zone=2, subtotal=500) == Decimal("0.00")


def test_no_free_shipping_just_below_threshold():
    assert cost(weight=2, zone=2, subtotal=149.99) == Decimal("13.75")


def test_no_free_shipping_zone3():
    assert cost(weight=2, zone=3, subtotal=1000) == Decimal("17.60")


def test_free_shipping_with_oversize_still_charges_surcharge():
    assert cost(weight=1, zone=1, subtotal=200, length_cm=121, width_cm=1, height_cm=1) == Decimal("12.00")


# ---- oversize surcharge ----

# Width/height of 1 cm keep volumetric weight tiny so only the length matters.
def test_oversize_surcharge_added():
    assert cost(weight=1, zone=1, length_cm=121, width_cm=1, height_cm=1) == Decimal("20.00")


def test_exactly_120_has_no_surcharge():
    assert cost(weight=1, zone=1, length_cm=120, width_cm=1, height_cm=1) == Decimal("8.00")


def test_longest_side_can_be_any_dimension():
    assert cost(weight=1, zone=1, length_cm=1, width_cm=121, height_cm=1) == Decimal("20.00")
    assert cost(weight=1, zone=1, length_cm=1, width_cm=1, height_cm=121) == Decimal("20.00")


def test_oversize_surcharge_not_multiplied_by_zone():
    # zone 3: 8 * 1.6 = 12.80, plus 12.00 surcharge = 24.80
    assert cost(weight=1, zone=3, length_cm=121, width_cm=1, height_cm=1) == Decimal("24.80")


# ---- invalid inputs: types ----

@pytest.mark.parametrize("bad", ["5", None, [1], True, object()])
def test_non_number_raises_type_error(bad):
    with pytest.raises(TypeError):
        shipping_cost(bad, 10, 10, 1, 1, 0)


@pytest.mark.parametrize(
    "args",
    [
        (True, 10, 10, 1, 1, 0),
        (10, False, 10, 1, 1, 0),
        (10, 10, True, 1, 1, 0),
        (10, 10, 10, True, 1, 0),
        (10, 10, 10, 1, 1, False),
    ],
)
def test_bool_in_numeric_argument_raises_type_error(args):
    with pytest.raises(TypeError):
        shipping_cost(*args)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), Decimal("NaN"), Decimal("Infinity")])
def test_non_finite_numbers_raise_value_error(bad):
    with pytest.raises(ValueError):
        shipping_cost(10, 10, 10, bad, 1, 0)
    with pytest.raises(ValueError):
        shipping_cost(bad, 10, 10, 1, 1, 0)
    with pytest.raises(ValueError):
        shipping_cost(10, 10, 10, 1, 1, bad)


# ---- invalid inputs: values ----

@pytest.mark.parametrize("field", ["length_cm", "width_cm", "height_cm", "weight_kg"])
@pytest.mark.parametrize("value", [0, -1, 0.0, Decimal("-0.5")])
def test_non_positive_dimension_or_weight_raises(field, value):
    kwargs = dict(length_cm=10, width_cm=10, height_cm=10, weight_kg=1)
    kwargs[field] = value
    with pytest.raises(ValueError):
        shipping_cost(kwargs["length_cm"], kwargs["width_cm"], kwargs["height_cm"],
                      kwargs["weight_kg"], 1, 0)


def test_negative_subtotal_raises():
    with pytest.raises(ValueError):
        shipping_cost(10, 10, 10, 1, 1, -0.01)


def test_zero_subtotal_is_allowed():
    assert shipping_cost(10, 10, 10, 1, 1, 0) == Decimal("8.00")


@pytest.mark.parametrize("zone", [0, 4, -1, True, False, 1.0, 2.0, "1", None])
def test_invalid_zone_raises_value_error(zone):
    with pytest.raises(ValueError):
        shipping_cost(10, 10, 10, 1, zone, 0)
