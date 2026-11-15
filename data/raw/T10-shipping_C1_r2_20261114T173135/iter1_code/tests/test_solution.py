from decimal import Decimal

import pytest

from solution import shipping_cost


def cost(length=10, width=10, height=10, weight=1, zone=1, subtotal=0):
    return shipping_cost(length, width, height, weight, zone, subtotal)


# --- return type and formatting -------------------------------------------

def test_returns_decimal_with_two_places():
    result = cost()
    assert isinstance(result, Decimal)
    assert str(result) == "8.00"


# --- billable weight and base charge --------------------------------------

@pytest.mark.parametrize(
    "weight, expected",
    [
        (0.3, "8.00"),    # rounds up to 0.5 -> first kg price
        (0.5, "8.00"),    # exact multiple stays
        (1, "8.00"),
        (1.2, "9.50"),    # rounds up to 1.5
        (1.5, "9.50"),
        (2, "11.00"),
        (2.1, "12.50"),   # rounds up to 2.5
        (3, "14.00"),
    ],
)
def test_base_charge_by_weight(weight, expected):
    assert str(cost(weight=weight)) == expected


def test_volumetric_weight_can_dominate():
    # 50 * 40 * 30 / 5000 = 12 kg, weight 1 kg is ignored
    assert str(cost(50, 40, 30, weight=1)) == "41.00"


def test_volumetric_weight_exact_multiple():
    # 100 * 50 * 20 / 5000 = 20 kg
    assert str(cost(100, 50, 20, weight=1)) == "65.00"


def test_volumetric_weight_rounds_up_but_is_small():
    # 10 * 10 * 15 / 5000 = 0.3 kg -> billable 0.5 kg
    assert str(cost(10, 10, 15, weight=0.1)) == "8.00"


def test_actual_weight_dominates_volumetric():
    # volumetric 0.2 kg, actual 3 kg
    assert str(cost(10, 10, 10, weight=3)) == "14.00"


def test_very_large_weight_keeps_precision():
    result = cost(weight=10**30)
    assert result == Decimal("3000000000000000000000000000005.00")


# --- zone factors ---------------------------------------------------------

@pytest.mark.parametrize(
    "zone, weight, expected",
    [
        (1, 1, "8.00"),
        (2, 1, "10.00"),
        (3, 1, "12.80"),
        (1, 1.5, "9.50"),
        (2, 1.5, "11.88"),   # 9.50 * 1.25 = 11.875 -> ROUND_HALF_UP
        (3, 1.5, "15.20"),
    ],
)
def test_zone_factors(zone, weight, expected):
    assert str(cost(weight=weight, zone=zone)) == expected


# --- free shipping --------------------------------------------------------

def test_free_shipping_zone1_at_threshold():
    assert str(cost(zone=1, subtotal=150)) == "0.00"


def test_free_shipping_zone2_above_threshold():
    assert str(cost(zone=2, subtotal=200)) == "0.00"


def test_no_free_shipping_below_threshold():
    assert str(cost(zone=1, subtotal=149.99)) == "8.00"


def test_no_free_shipping_zone3():
    assert str(cost(zone=3, subtotal=200)) == "12.80"


# --- oversize surcharge ---------------------------------------------------

# Thin parcels keep volumetric weight tiny so only the surcharge is tested.

def test_no_surcharge_at_120_cm():
    assert str(cost(120, 1, 1)) == "8.00"


def test_surcharge_above_120_cm():
    assert str(cost(121, 1, 1)) == "20.00"


def test_surcharge_uses_longest_side_any_axis():
    assert str(cost(1, 1, 121)) == "20.00"
    assert str(cost(1, 121, 1)) == "20.00"


def test_surcharge_not_multiplied_by_zone_factor():
    # 8.00 * 1.6 = 12.80, plus flat 12.00
    assert str(cost(121, 1, 1, zone=3)) == "24.80"


def test_surcharge_not_waived_by_free_shipping():
    assert str(cost(121, 1, 1, zone=1, subtotal=150)) == "12.00"


# --- input types ----------------------------------------------------------

def test_decimal_inputs_are_accepted():
    assert str(shipping_cost(Decimal("10"), Decimal("10"), Decimal("10"),
                             Decimal("1.5"), 1, Decimal("150.00"))) == "0.00"
    assert str(cost(weight=Decimal("1.5"))) == "9.50"


def test_float_is_converted_through_str():
    # 0.1 kg as float must behave exactly like Decimal("0.1")
    assert cost(weight=0.1) == cost(weight=Decimal("0.1"))
    assert str(cost(weight=1.5, zone=2)) == "11.88"


def test_float_subtotal_threshold():
    assert str(cost(zone=1, subtotal=150.0)) == "0.00"


@pytest.mark.parametrize(
    "args",
    [
        ("10", 10, 10, 1, 1, 0),
        (10, None, 10, 1, 1, 0),
        (10, 10, [10], 1, 1, 0),
        (10, 10, 10, "1", 1, 0),
        (10, 10, 10, 1, 1, "0"),
        (True, 10, 10, 1, 1, 0),
        (10, False, 10, 1, 1, 0),
        (10, 10, True, 1, 1, 0),
        (10, 10, 10, True, 1, 0),
        (10, 10, 10, 1, 1, False),
    ],
)
def test_non_numbers_raise_type_error(args):
    with pytest.raises(TypeError):
        shipping_cost(*args)


@pytest.mark.parametrize(
    "args",
    [
        (0, 10, 10, 1, 1, 0),
        (10, -1, 10, 1, 1, 0),
        (10, 10, 0.0, 1, 1, 0),
        (10, 10, 10, 0, 1, 0),
        (10, 10, 10, -1, 1, 0),
        (10, 10, 10, 1, 1, -0.01),
        (float("nan"), 10, 10, 1, 1, 0),
        (10, 10, 10, float("inf"), 1, 0),
        (10, 10, 10, 1, 1, Decimal("NaN")),
        (10, 10, 10, 1, 1, Decimal("-Infinity")),
    ],
)
def test_out_of_range_values_raise_value_error(args):
    with pytest.raises(ValueError):
        shipping_cost(*args)


@pytest.mark.parametrize("zone", [0, 4, -1, "1", 1.0, 2.0, True, None, [1]])
def test_invalid_zone_raises_value_error(zone):
    with pytest.raises(ValueError):
        cost(zone=zone)
