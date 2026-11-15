from decimal import Decimal

import pytest

from solution import _to_decimal, shipping_cost


def cost(length=10, width=10, height=10, weight=1, zone=1, subtotal=0):
    return shipping_cost(length, width, height, weight, zone, subtotal)


# --- result format -------------------------------------------------------

def test_returns_decimal_with_two_places():
    result = cost()
    assert isinstance(result, Decimal)
    assert result == Decimal("8.00")
    assert str(result) == "8.00"
    assert result.as_tuple().exponent == -2


def test_zero_result_has_two_places():
    result = cost(zone=1, subtotal=150)
    assert isinstance(result, Decimal)
    assert str(result) == "0.00"


# --- billable weight and base charge -------------------------------------

@pytest.mark.parametrize(
    "weight, expected",
    [
        (0.5, "8.00"),   # 0.5 kg costs 8.00
        (1, "8.00"),     # 1 kg costs 8.00
        (1.2, "9.50"),   # rounds up to 1.5 kg
        (1.01, "9.50"),  # rounds up to 1.5 kg
        (1.5, "9.50"),
        (2, "11.00"),
        (2.1, "12.50"),  # rounds up to 2.5 kg
        (3, "14.00"),
    ],
)
def test_actual_weight_rounded_up_to_half_kg(weight, expected):
    assert cost(weight=weight) == Decimal(expected)


def test_volumetric_weight_dominates():
    # 50 * 50 * 50 / 5000 = 25 kg -> 8 + 48 steps * 1.50 = 80.00
    assert cost(50, 50, 50, weight=1) == Decimal("80.00")


def test_volumetric_weight_rounded_up():
    # 10 * 10 * 101 / 5000 = 2.02 kg -> 2.5 kg -> 8 + 3 * 1.50 = 12.50
    assert cost(10, 10, 101, weight=1) == Decimal("12.50")


def test_actual_weight_dominates_volumetric():
    assert cost(10, 10, 10, weight=3) == Decimal("14.00")


def test_volumetric_is_not_used_when_smaller():
    # volumetric 0.2 kg is smaller than actual 2 kg
    assert cost(10, 10, 10, weight=2) == Decimal("11.00")


def test_billable_weight_exact_multiple_stays():
    assert cost(weight=2.5) == Decimal("12.50")


# --- zone factors ---------------------------------------------------------

@pytest.mark.parametrize(
    "zone, expected",
    [
        (1, "8.00"),
        (2, "10.00"),
        (3, "12.80"),
    ],
)
def test_zone_factor_applied(zone, expected):
    assert cost(zone=zone) == Decimal(expected)


def test_zone_factor_on_larger_charge():
    assert cost(weight=1.5, zone=3) == Decimal("15.20")
    assert cost(weight=2, zone=2) == Decimal("13.75")


def test_zone2_rounding_half_up_rounds_up_on_tie():
    # 9.50 * 1.25 = 11.875 -> 11.88
    assert cost(weight=1.5, zone=2) == Decimal("11.88")


def test_zone2_rounding_half_up_exact_tie_at_even_digit():
    # 12.50 * 1.25 = 15.625 -> 15.63 (banker's rounding would give 15.62)
    assert cost(weight=2.5, zone=2) == Decimal("15.63")


# --- free shipping --------------------------------------------------------

def test_free_shipping_zone1_at_threshold():
    assert cost(zone=1, subtotal=150) == Decimal("0.00")


def test_free_shipping_zone2_above_threshold():
    assert cost(zone=2, subtotal=200) == Decimal("0.00")


def test_no_free_shipping_just_below_threshold():
    assert cost(zone=1, subtotal=149.99) == Decimal("8.00")


def test_no_free_shipping_zone3():
    assert cost(zone=3, subtotal=150) == Decimal("12.80")


def test_free_shipping_with_decimal_subtotal():
    assert cost(zone=1, subtotal=Decimal("150.00")) == Decimal("0.00")


# --- oversize surcharge ---------------------------------------------------

def test_oversize_adds_twelve():
    assert cost(121, 1, 1, weight=1) == Decimal("20.00")


def test_oversize_at_limit_not_applied():
    assert cost(120, 1, 1, weight=1) == Decimal("8.00")


def test_oversize_on_width():
    assert cost(1, 121, 1, weight=1) == Decimal("20.00")


def test_oversize_on_height():
    assert cost(1, 1, 121, weight=1) == Decimal("20.00")


def test_oversize_not_multiplied_by_zone():
    # 8 * 1.6 = 12.80, plus 12.00 surcharge
    assert cost(121, 1, 1, weight=1, zone=3) == Decimal("24.80")


def test_oversize_not_waived_by_free_shipping():
    assert cost(121, 1, 1, weight=1, zone=1, subtotal=150) == Decimal("12.00")


# --- numeric input types --------------------------------------------------

def test_decimal_inputs_accepted():
    result = shipping_cost(
        Decimal("10"), Decimal("10"), Decimal("10"), Decimal("1.5"), 1, Decimal("0")
    )
    assert result == Decimal("9.50")


def test_mixed_int_float_decimal_inputs():
    result = shipping_cost(10, 10.0, Decimal("10"), 1.5, 2, 0.0)
    assert result == Decimal("11.88")


@pytest.mark.parametrize("bad", [True, False, "1", None, [1], (1,), {"a": 1}])
@pytest.mark.parametrize("position", range(5))
def test_non_number_raises_type_error(bad, position):
    args = [10, 10, 10, 1, 1, 0]
    # positions 0-4 are the numeric arguments other than zone
    numeric_positions = [0, 1, 2, 3, 5]
    args[numeric_positions[position]] = bad
    with pytest.raises(TypeError):
        shipping_cost(*args)


@pytest.mark.parametrize("index", [0, 1, 2, 3, 5])
def test_bool_numeric_argument_raises_type_error(index):
    args = [10, 10, 10, 1, 1, 0]
    args[index] = True
    with pytest.raises(TypeError):
        shipping_cost(*args)


# --- value validation -----------------------------------------------------

@pytest.mark.parametrize("index", [0, 1, 2, 3])
@pytest.mark.parametrize("value", [0, -1, -0.5, Decimal("0")])
def test_dimensions_and_weight_must_be_positive(index, value):
    args = [10, 10, 10, 1, 1, 0]
    args[index] = value
    with pytest.raises(ValueError):
        shipping_cost(*args)


@pytest.mark.parametrize("value", [-1, -0.01, Decimal("-5")])
def test_subtotal_must_not_be_negative(value):
    with pytest.raises(ValueError):
        cost(subtotal=value)


def test_subtotal_zero_is_allowed():
    assert cost(subtotal=0) == Decimal("8.00")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), Decimal("NaN")])
def test_non_finite_values_rejected(value):
    with pytest.raises(ValueError):
        cost(length=value)
    with pytest.raises(ValueError):
        cost(weight=value)
    with pytest.raises(ValueError):
        cost(subtotal=value)


@pytest.mark.parametrize("zone", [0, 4, -1, True, False, 1.0, 2.0, "1", None])
def test_invalid_zone_raises_value_error(zone):
    with pytest.raises(ValueError):
        cost(zone=zone)


# --- float conversion helper ----------------------------------------------

def test_float_converted_through_str():
    assert _to_decimal(0.1, "x") == Decimal("0.1")
    assert _to_decimal(0.1, "x") != Decimal(0.1)


def test_int_and_decimal_pass_through():
    assert _to_decimal(7, "x") == Decimal(7)
    assert _to_decimal(Decimal("2.50"), "x") == Decimal("2.50")


def test_float_zero_point_one_weight_is_exact():
    # 0.1 kg is treated as exactly 0.1 kg, so billable weight is 0.5 kg
    assert cost(weight=0.1) == Decimal("8.00")
