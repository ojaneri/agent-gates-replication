from decimal import Decimal

import pytest

from solution import shipping_cost


def cost(length=10, width=10, height=10, weight=0.5, zone=1, subtotal=0):
    return shipping_cost(length, width, height, weight, zone, subtotal)


# --- base charge and billable weight -------------------------------------

@pytest.mark.parametrize(
    "weight, expected",
    [
        (0.5, "8.00"),
        (1, "8.00"),
        (1.2, "9.50"),
        (1.5, "9.50"),
        (1.6, "11.00"),
        (2, "11.00"),
        (2.5, "12.50"),
        (25, "80.00"),
    ],
)
def test_base_charge_by_billable_weight(weight, expected):
    assert cost(weight=weight) == Decimal(expected)


def test_returns_decimal_with_two_places():
    result = cost(weight=0.5)
    assert isinstance(result, Decimal)
    assert str(result) == "8.00"


def test_decimal_and_int_inputs_are_accepted():
    assert cost(weight=Decimal("1.2")) == Decimal("9.50")
    assert cost(length=10, width=10, height=10, weight=1, zone=1, subtotal=0) == Decimal("8.00")


def test_float_is_converted_through_str():
    assert cost(weight=0.1) == Decimal("8.00")
    assert cost(weight=1.0000000001) == Decimal("9.50")


def test_volumetric_weight_dominates_when_larger():
    # 50 * 50 * 50 / 5000 = 25 kg
    assert cost(50, 50, 50, weight=1) == Decimal("80.00")


def test_volumetric_weight_exactly_two_kg():
    # 10 * 10 * 100 / 5000 = 2 kg -> stays 2 kg -> 11.00
    assert cost(10, 10, 100, weight=1) == Decimal("11.00")


def test_volumetric_weight_just_above_two_kg_rounds_up():
    # 10 * 10 * 101 / 5000 = 2.02 kg -> 2.5 kg -> 12.50
    assert cost(10, 10, 101, weight=1) == Decimal("12.50")


def test_small_volumetric_weight_does_not_reduce_actual_weight():
    # volumetric 0.2 kg, actual 1.2 kg -> 1.5 kg -> 9.50
    assert cost(10, 10, 10, weight=1.2) == Decimal("9.50")


# --- zone factors and rounding -------------------------------------------

def test_zone_two_factor_with_rounding_half_up():
    # 9.50 * 1.25 = 11.875 -> 11.88
    assert cost(weight=1.5, zone=2) == Decimal("11.88")


def test_zone_two_half_up_on_exact_half_cent():
    # 12.50 * 1.25 = 15.625 -> 15.63 (ROUND_HALF_EVEN would give 15.62)
    assert cost(weight=2.5, zone=2) == Decimal("15.63")


def test_zone_three_factor():
    # 9.50 * 1.6 = 15.20
    assert cost(weight=1.5, zone=3) == Decimal("15.20")


def test_zone_three_factor_on_one_kg():
    assert cost(weight=1, zone=3) == Decimal("12.80")


def test_zone_one_factor_is_one():
    assert cost(weight=2.5, zone=1) == Decimal("12.50")


# --- free shipping --------------------------------------------------------

def test_free_shipping_zone_one_at_150():
    assert cost(weight=5, zone=1, subtotal=150) == Decimal("0.00")


def test_free_shipping_zone_two_above_150():
    assert cost(weight=5, zone=2, subtotal=200) == Decimal("0.00")


def test_no_free_shipping_just_below_150():
    assert cost(weight=0.5, zone=1, subtotal=149.99) == Decimal("8.00")


def test_no_free_shipping_in_zone_three():
    assert cost(weight=0.5, zone=3, subtotal=1000) == Decimal("12.80")


def test_subtotal_zero_is_allowed_and_not_free():
    assert cost(weight=0.5, zone=1, subtotal=0) == Decimal("8.00")


def test_float_subtotal_at_threshold():
    assert cost(weight=0.5, zone=2, subtotal=150.0) == Decimal("0.00")


# --- oversize surcharge ---------------------------------------------------

def test_oversize_length_adds_surcharge():
    # volumetric 121 / 5000 kg is tiny, so billable stays 0.5 kg
    assert cost(length=121, width=1, height=1, weight=0.5) == Decimal("20.00")


def test_length_exactly_120_has_no_surcharge():
    assert cost(length=120, width=1, height=1, weight=0.5) == Decimal("8.00")


def test_oversize_width_adds_surcharge():
    assert cost(length=1, width=121, height=1, weight=1) == Decimal("20.00")


def test_oversize_height_adds_surcharge():
    assert cost(length=1, width=1, height=121, weight=1) == Decimal("20.00")


def test_surcharge_not_multiplied_by_zone_factor():
    # 8.00 * 1.6 = 12.80, plus 12.00 surcharge
    assert cost(length=121, width=1, height=1, weight=0.5, zone=3) == Decimal("24.80")


def test_surcharge_not_waived_by_free_shipping():
    assert cost(length=121, width=1, height=1, weight=0.5, zone=1, subtotal=150) == Decimal("12.00")


def test_surcharge_with_zone_two_factor_and_rounding():
    # 9.50 * 1.25 = 11.875, plus 12.00 = 23.875 -> 23.88
    assert cost(length=121, width=1, height=1, weight=1.5, zone=2) == Decimal("23.88")


# --- input validation -----------------------------------------------------

@pytest.mark.parametrize("bad", [True, False, "10", None, [10], object()])
def test_non_number_dimension_raises_type_error(bad):
    with pytest.raises(TypeError):
        cost(length=bad)


@pytest.mark.parametrize("name", ["width", "height", "weight", "subtotal"])
def test_bool_or_string_in_other_numeric_args_raises_type_error(name):
    kwargs = {"length": 10, "width": 10, "height": 10, "weight": 0.5, "subtotal": 0}
    kwargs[name] = True
    with pytest.raises(TypeError):
        shipping_cost(kwargs["length"], kwargs["width"], kwargs["height"],
                      kwargs["weight"], 1, kwargs["subtotal"])
    kwargs[name] = "1"
    with pytest.raises(TypeError):
        shipping_cost(kwargs["length"], kwargs["width"], kwargs["height"],
                      kwargs["weight"], 1, kwargs["subtotal"])


@pytest.mark.parametrize("bad", [0, -1, -0.5])
def test_dimensions_must_be_positive(bad):
    with pytest.raises(ValueError):
        cost(length=bad)
    with pytest.raises(ValueError):
        cost(width=bad)
    with pytest.raises(ValueError):
        cost(height=bad)


@pytest.mark.parametrize("bad", [0, -0.1])
def test_weight_must_be_positive(bad):
    with pytest.raises(ValueError):
        cost(weight=bad)


def test_smallest_positive_weight_is_accepted():
    assert cost(weight=0.0001) == Decimal("8.00")


def test_negative_subtotal_raises():
    with pytest.raises(ValueError):
        cost(subtotal=-0.01)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), Decimal("NaN")])
def test_non_finite_numbers_raise_value_error(bad):
    with pytest.raises(ValueError):
        cost(length=bad)
    with pytest.raises(ValueError):
        cost(weight=bad)
    with pytest.raises(ValueError):
        cost(subtotal=bad)


@pytest.mark.parametrize("bad", [0, 4, -1, 1.0, 2.0, "1", True, False, None])
def test_zone_must_be_int_one_two_or_three(bad):
    with pytest.raises(ValueError):
        cost(zone=bad)


@pytest.mark.parametrize("good", [1, 2, 3])
def test_valid_zones_are_accepted(good):
    assert cost(zone=good, weight=0.5) in (Decimal("8.00"), Decimal("10.00"), Decimal("12.80"))
