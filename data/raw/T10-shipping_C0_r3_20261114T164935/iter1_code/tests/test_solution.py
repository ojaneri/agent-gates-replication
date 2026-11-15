from decimal import Decimal

import pytest

from solution import shipping_cost


SMALL = (10, 10, 10)  # volumetric weight 0.2 kg


def cost(weight=1, zone=1, subtotal=0, dims=SMALL):
    return shipping_cost(*dims, weight, zone, subtotal)


# Base charge and billable weight rounding

def test_returns_decimal_with_two_places():
    result = cost()
    assert isinstance(result, Decimal)
    assert str(result) == "8.00"


@pytest.mark.parametrize(
    "weight, expected",
    [
        (0.1, "8.00"),
        (0.5, "8.00"),
        (1, "8.00"),
        (1.2, "9.50"),   # rounds up to 1.5 kg
        (1.5, "9.50"),
        (2, "11.00"),
        (2.5, "12.50"),
    ],
)
def test_base_charge_by_billable_weight(weight, expected):
    assert str(cost(weight=weight)) == expected


def test_volumetric_weight_can_be_billable():
    # 50 * 50 * 40 / 5000 = 20 kg -> 8 + 1.5 * 38 = 65.00
    assert str(cost(weight=1, dims=(50, 50, 40))) == "65.00"


def test_volumetric_exact_half_kg_is_not_rounded_up_further():
    # 10 * 10 * 25 / 5000 = 0.5 kg, a multiple of 0.5 -> 8.00
    assert str(cost(weight=0.1, dims=(10, 10, 25))) == "8.00"


def test_actual_weight_wins_when_larger_than_volumetric():
    # volumetric 0.2 kg, actual 3 kg -> 8 + 1.5 * 4 = 14.00
    assert str(cost(weight=3)) == "14.00"


# Zone factors

@pytest.mark.parametrize(
    "zone, expected",
    [(1, "8.00"), (2, "10.00"), (3, "12.80")],
)
def test_zone_factor(zone, expected):
    assert str(cost(zone=zone)) == expected


# Free shipping

def test_free_shipping_zone_1_at_150():
    assert str(cost(zone=1, subtotal=150)) == "0.00"


def test_free_shipping_zone_2_above_150():
    assert str(cost(zone=2, subtotal=200)) == "0.00"


def test_no_free_shipping_zone_3():
    assert str(cost(zone=3, subtotal=200)) == "12.80"


def test_no_free_shipping_just_below_threshold():
    assert str(cost(zone=1, subtotal=Decimal("149.99"))) == "8.00"


def test_free_shipping_accepts_decimal_subtotal():
    assert str(cost(zone=1, subtotal=Decimal("150"))) == "0.00"


# Oversize surcharge

def test_oversize_adds_12_when_longest_side_above_120():
    # thin box keeps volumetric weight tiny: 121 * 1 * 1 / 5000 is well under 0.5 kg
    assert str(cost(dims=(121, 1, 1))) == "20.00"


def test_no_oversize_at_exactly_120():
    assert str(cost(dims=(120, 1, 1))) == "8.00"


def test_oversize_not_multiplied_by_zone_factor():
    # zone 3: 8 * 1.6 = 12.80, plus 12.00 -> 24.80
    assert str(cost(zone=3, dims=(130, 1, 1))) == "24.80"


def test_oversize_not_waived_by_free_shipping():
    assert str(cost(zone=1, subtotal=200, dims=(130, 1, 1))) == "12.00"


# Rounding

def test_round_half_up_zone_2():
    # 9.50 * 1.25 = 11.875 -> 11.88
    assert str(cost(weight=1.5, zone=2)) == "11.88"


def test_round_half_up_zone_2_larger():
    # 12.50 * 1.25 = 15.625 -> 15.63
    assert str(cost(weight=2.5, zone=2)) == "15.63"


def test_zone_3_exact_value():
    # 9.50 * 1.6 = 15.20
    assert str(cost(weight=1.5, zone=3)) == "15.20"


# Float and Decimal conversion

def test_float_converted_through_str():
    # str(1.0000000000000002) is above 1 kg, so it bills at 1.5 kg
    assert str(cost(weight=1.0000000000000002)) == "9.50"


def test_decimal_inputs_accepted():
    result = shipping_cost(Decimal("10"), Decimal("10"), Decimal("10"), Decimal("1"), 1, Decimal("0"))
    assert str(result) == "8.00"


# Type errors

@pytest.mark.parametrize(
    "bad",
    ["1", None, [1], True, complex(1, 1)],
)
def test_non_number_raises_type_error(bad):
    with pytest.raises(TypeError):
        shipping_cost(bad, 10, 10, 1, 1, 0)
    with pytest.raises(TypeError):
        shipping_cost(10, 10, 10, bad, 1, 0)
    with pytest.raises(TypeError):
        shipping_cost(10, 10, 10, 1, 1, bad)


def test_bool_dimension_raises_type_error():
    with pytest.raises(TypeError):
        shipping_cost(True, 10, 10, 1, 1, 0)


# Value errors

@pytest.mark.parametrize("dims", [(0, 10, 10), (10, -1, 10), (10, 10, 0)])
def test_dimensions_must_be_positive(dims):
    with pytest.raises(ValueError):
        shipping_cost(*dims, 1, 1, 0)


@pytest.mark.parametrize("weight", [0, -0.5])
def test_weight_must_be_positive(weight):
    with pytest.raises(ValueError):
        cost(weight=weight)


def test_negative_subtotal_rejected():
    with pytest.raises(ValueError):
        cost(subtotal=-1)


def test_zero_subtotal_accepted():
    assert str(cost(subtotal=0)) == "8.00"


@pytest.mark.parametrize("bad_zone", [True, 1.0, "1", 0, 4, None, 2.0])
def test_invalid_zone_raises_value_error(bad_zone):
    with pytest.raises(ValueError):
        cost(zone=bad_zone)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), Decimal("NaN")])
def test_non_finite_numbers_rejected(bad):
    with pytest.raises(ValueError):
        cost(weight=bad)
