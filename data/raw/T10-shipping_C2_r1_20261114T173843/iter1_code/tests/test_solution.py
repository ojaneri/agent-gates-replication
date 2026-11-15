from decimal import Decimal

import pytest

from solution import shipping_cost


# ---- billable weight and base charge -------------------------------------

@pytest.mark.parametrize(
    "weight, expected",
    [
        (0.4, "8.00"),    # rounds up to 0.5 kg
        (0.5, "8.00"),
        (1, "8.00"),
        (1.0, "8.00"),
        (1.1, "9.50"),    # float 1.1 -> 1.5 kg
        (1.5, "9.50"),
        (2, "11.00"),
        (2.5, "12.50"),
        (3.2, "15.50"),   # rounds up to 3.5 kg
        (10, "35.00"),
        (Decimal("1.5"), "9.50"),
        (Decimal("2.0000001"), "12.50"),  # just over 2 kg rounds up to 2.5 kg
    ],
)
def test_weight_only_base_charge(weight, expected):
    result = shipping_cost(1, 1, 1, weight, 1, 0)
    assert result == Decimal(expected)


def test_result_is_decimal_with_two_places():
    result = shipping_cost(1, 1, 1, 1, 1, 0)
    assert isinstance(result, Decimal)
    assert str(result) == "8.00"
    assert result.as_tuple().exponent == -2


def test_int_dimensions_and_int_weight_accepted():
    assert shipping_cost(1, 1, 1, 2, 1, 0) == Decimal("11.00")


# ---- volumetric weight -----------------------------------------------------

def test_volumetric_weight_dominates_actual_weight():
    # 50*50*50/5000 = 25 kg billable -> 8 + 1.5 * 48 = 80.00
    assert shipping_cost(50, 50, 50, 1, 1, 0) == Decimal("80.00")


def test_volumetric_two_kg_exact():
    # 100*10*10/5000 = 2 kg -> 11.00
    assert shipping_cost(100, 10, 10, 1, 1, 0) == Decimal("11.00")


def test_volumetric_rounded_up_to_half_kg():
    # 30*20*20/5000 = 2.4 kg -> 2.5 kg -> 12.50
    assert shipping_cost(30, 20, 20, 2.0, 1, 0) == Decimal("12.50")


def test_volumetric_just_above_two_and_a_half_kg():
    # 47*19*14 = 12502 -> 2.5004 kg -> 3.0 kg -> 14.00
    assert shipping_cost(47, 19, 14, 1, 1, 0) == Decimal("14.00")


def test_volumetric_exactly_two_and_a_half_kg():
    # 25*20*25 = 12500 -> 2.5 kg -> 12.50
    assert shipping_cost(25, 20, 25, 1, 1, 0) == Decimal("12.50")


def test_actual_weight_dominates_volumetric():
    # 10*10*10/5000 = 0.2 kg; actual 3 kg -> 14.00
    assert shipping_cost(10, 10, 10, 3, 1, 0) == Decimal("14.00")


def test_volumetric_with_zone_factor():
    assert shipping_cost(47, 19, 14, 1, 3, 0) == Decimal("22.40")


def test_tiny_weight_and_tiny_volume_use_minimum_charge():
    assert shipping_cost(0.01, 0.01, 0.01, 0.01, 1, 0) == Decimal("8.00")


# ---- zone factors and rounding -------------------------------------------

def test_zone_two_factor():
    assert shipping_cost(1, 1, 1, 1, 2, 0) == Decimal("10.00")


def test_zone_three_factor():
    assert shipping_cost(1, 1, 1, 1, 3, 0) == Decimal("12.80")


def test_zone_three_with_one_and_a_half_kg():
    assert shipping_cost(1, 1, 1, 1.5, 3, 0) == Decimal("15.20")


def test_zone_two_with_one_and_a_half_kg_rounds_half_up():
    # 9.50 * 1.25 = 11.875 -> 11.88
    assert shipping_cost(1, 1, 1, 1.5, 2, 0) == Decimal("11.88")


def test_zone_two_half_up_not_bankers_rounding():
    # 12.50 * 1.25 = 15.625 -> 15.63 (ROUND_HALF_EVEN would give 15.62)
    assert shipping_cost(1, 1, 1, 2.5, 2, 0) == Decimal("15.63")


def test_zone_three_exact_twenty():
    assert shipping_cost(1, 1, 1, 2.5, 3, 0) == Decimal("20.00")


def test_zone_one_with_two_and_a_half_kg():
    assert shipping_cost(1, 1, 1, 2.5, 1, 0) == Decimal("12.50")


# ---- free shipping ----------------------------------------------------------

@pytest.mark.parametrize(
    "zone, subtotal, expected",
    [
        (1, 150, "0.00"),
        (2, 150, "0.00"),
        (1, 150.0, "0.00"),
        (1, Decimal("1000"), "0.00"),
        (2, 149.99, "10.00"),
        (1, 149.99, "8.00"),
        (1, 0, "8.00"),
        (3, 150, "12.80"),
        (3, 1000, "12.80"),
    ],
)
def test_free_shipping_only_for_zones_one_and_two_at_150(zone, subtotal, expected):
    result = shipping_cost(1, 1, 1, 1, zone, subtotal)
    assert result == Decimal(expected)


def test_free_shipping_with_heavy_parcel_is_zero():
    assert shipping_cost(1, 1, 1, 3, 1, 150) == Decimal("0.00")


def test_free_shipping_still_pays_oversize_surcharge():
    assert shipping_cost(121, 1, 1, 1, 1, 200) == Decimal("12.00")


# ---- oversize surcharge -----------------------------------------------------

def test_length_exactly_120_has_no_surcharge():
    assert shipping_cost(120, 1, 1, 1, 1, 0) == Decimal("8.00")


def test_length_just_over_120_adds_surcharge():
    assert shipping_cost(120.01, 1, 1, 1, 1, 0) == Decimal("20.00")


def test_width_over_120_zone_three_surcharge_not_multiplied():
    # 12.80 + 12.00
    assert shipping_cost(1, 121, 1, 1, 3, 0) == Decimal("24.80")


def test_height_over_120_zone_two_surcharge():
    assert shipping_cost(1, 1, 121, 1, 2, 0) == Decimal("22.00")


def test_oversize_with_volumetric_weight():
    # 130*10*10 = 13000/5000 = 2.6 -> 3.0 kg -> 14.00, +12 surcharge
    assert shipping_cost(130, 10, 10, 1, 1, 0) == Decimal("26.00")


# ---- input types -------------------------------------------------------------

@pytest.mark.parametrize(
    "args",
    [
        ("10", 1, 1, 1, 1, 0),
        (1, None, 1, 1, 1, 0),
        (1, 1, [1], 1, 1, 0),
        (True, 1, 1, 1, 1, 0),
        (1, 1, 1, True, 1, 0),
        (1, 1, 1, 1, 1, True),
        (1, 1, 1, 1, 1, "0"),
        (1, 1, 1, 1j, 1, 0),
        (1, 1, 1, 1, 1, None),
    ],
)
def test_non_numbers_raise_type_error(args):
    with pytest.raises(TypeError):
        shipping_cost(*args)


@pytest.mark.parametrize(
    "args",
    [
        (0, 1, 1, 1, 1, 0),
        (1, 0, 1, 1, 1, 0),
        (1, 1, 0, 1, 1, 0),
        (-1, 1, 1, 1, 1, 0),
        (1, 1, 1, 0, 1, 0),
        (1, 1, 1, -0.5, 1, 0),
        (1, 1, 1, 1, 1, -0.01),
        (float("nan"), 1, 1, 1, 1, 0),
        (1, 1, float("inf"), 1, 1, 0),
        (1, 1, 1, Decimal("NaN"), 1, 0),
        (1, 1, 1, 1, 1, Decimal("-Infinity")),
    ],
)
def test_out_of_range_numbers_raise_value_error(args):
    with pytest.raises(ValueError):
        shipping_cost(*args)


@pytest.mark.parametrize("zone", [0, 4, -1, True, False, 1.0, 2.0, "1", None, Decimal(1)])
def test_invalid_zone_raises_value_error(zone):
    with pytest.raises(ValueError):
        shipping_cost(1, 1, 1, 1, zone, 0)


@pytest.mark.parametrize("zone", [1, 2, 3])
def test_valid_zones_accepted(zone):
    assert isinstance(shipping_cost(1, 1, 1, 1, zone, 0), Decimal)


def test_subtotal_zero_is_allowed():
    assert shipping_cost(1, 1, 1, 1, 1, 0) == Decimal("8.00")
