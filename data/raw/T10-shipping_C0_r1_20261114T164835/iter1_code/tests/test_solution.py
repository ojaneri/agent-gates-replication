from decimal import Decimal

import pytest

from solution import shipping_cost


def cost(l=10, w=10, h=10, wt=1, zone=1, sub=0):
    return shipping_cost(l, w, h, wt, zone, sub)


# --- base charge and billable weight ---

def test_first_kg_costs_8_in_zone_1():
    assert cost(wt=1) == Decimal("8.00")


def test_half_kg_costs_8():
    assert cost(wt=0.5) == Decimal("8.00")


def test_1_5_kg_costs_9_50():
    assert cost(wt=1.5) == Decimal("9.50")


def test_2_kg_costs_11():
    assert cost(wt=2) == Decimal("11.00")


def test_result_has_two_decimal_places():
    result = cost(wt=1)
    assert isinstance(result, Decimal)
    assert str(result) == "8.00"
    assert result.as_tuple().exponent == -2


def test_float_0_1_is_treated_as_exact_decimal():
    assert cost(wt=0.1) == Decimal("8.00")


def test_decimal_input_accepted():
    assert cost(wt=Decimal("1.5")) == Decimal("9.50")


def test_volumetric_weight_dominates():
    # 50*50*40 / 5000 = 20 kg -> 8 + 1.5 * 38 = 65.00
    assert cost(50, 50, 40, 1) == Decimal("65.00")


def test_volumetric_weight_rounded_up_to_half_kg():
    # 50*101*10 = 50500 / 5000 = 10.1 kg -> rounds up to 10.5 -> 8 + 1.5*19 = 36.50
    assert cost(50, 101, 10, 1) == Decimal("36.50")


def test_actual_weight_dominates_when_larger():
    # volumetric 0.2 kg, actual 3 kg -> billable 3 -> 8 + 1.5*4 = 14.00
    assert cost(10, 10, 10, 3) == Decimal("14.00")


def test_small_volume_and_light_weight_bill_as_half_kg():
    assert cost(1, 1, 1, 0.01) == Decimal("8.00")


# --- zone factors ---

def test_zone_2_factor():
    assert cost(wt=1, zone=2) == Decimal("10.00")


def test_zone_3_factor():
    assert cost(wt=1, zone=3) == Decimal("12.80")


def test_zone_3_factor_on_1_5_kg():
    assert cost(wt=1.5, zone=3) == Decimal("15.20")


def test_zone_2_rounding_half_up():
    # 9.50 * 1.25 = 11.875 -> 11.88 with ROUND_HALF_UP
    assert cost(wt=1.5, zone=2) == Decimal("11.88")


# --- free shipping ---

def test_free_shipping_zone_1_at_150():
    assert cost(wt=1, zone=1, sub=150) == Decimal("0.00")


def test_free_shipping_zone_2_above_150():
    assert cost(wt=2, zone=2, sub=200) == Decimal("0.00")


def test_no_free_shipping_just_below_150():
    assert cost(wt=1, zone=1, sub=149.99) == Decimal("8.00")


def test_zone_3_not_waived_by_free_shipping():
    assert cost(wt=1, zone=3, sub=500) == Decimal("12.80")


def test_free_shipping_with_float_150():
    assert cost(wt=1, zone=1, sub=150.0) == Decimal("0.00")


# --- oversize surcharge ---

def test_oversize_adds_12_when_longest_side_above_120():
    assert cost(121, 1, 1, 1) == Decimal("20.00")


def test_no_surcharge_at_exactly_120():
    assert cost(120, 1, 1, 1) == Decimal("8.00")


def test_oversize_surcharge_not_multiplied_by_zone():
    # zone 3: 12.80 + 12.00 = 24.80
    assert cost(121, 1, 1, 1, zone=3) == Decimal("24.80")


def test_oversize_surcharge_not_waived_by_free_shipping():
    assert cost(130, 10, 10, 1, zone=1, sub=150) == Decimal("12.00")


def test_oversize_uses_largest_side_regardless_of_position():
    assert cost(1, 1, 130, 1) == Decimal("20.00")
    assert cost(1, 130, 1, 1) == Decimal("20.00")


# --- rounding ---

def test_total_is_rounded_half_up_to_cents():
    assert cost(wt=1.5, zone=2) == Decimal("11.88")


# --- type errors ---

@pytest.mark.parametrize("bad", [True, False, "10", None, [10]])
def test_non_numeric_dimension_raises_type_error(bad):
    with pytest.raises(TypeError):
        shipping_cost(bad, 10, 10, 1, 1, 0)


def test_bool_weight_raises_type_error():
    with pytest.raises(TypeError):
        shipping_cost(10, 10, 10, True, 1, 0)


def test_string_subtotal_raises_type_error():
    with pytest.raises(TypeError):
        shipping_cost(10, 10, 10, 1, 1, "0")


def test_bool_subtotal_raises_type_error():
    with pytest.raises(TypeError):
        shipping_cost(10, 10, 10, 1, 1, False)


# --- zone validation ---

@pytest.mark.parametrize("zone", [True, 1.0, "1", 0, 4, -1, None])
def test_invalid_zone_raises_value_error(zone):
    with pytest.raises(ValueError):
        shipping_cost(10, 10, 10, 1, zone, 0)


# --- value validation ---

@pytest.mark.parametrize("dim", [0, -5])
def test_non_positive_dimension_raises(dim):
    with pytest.raises(ValueError):
        shipping_cost(dim, 10, 10, 1, 1, 0)


def test_zero_weight_raises():
    with pytest.raises(ValueError):
        cost(wt=0)


def test_negative_weight_raises():
    with pytest.raises(ValueError):
        cost(wt=-1)


def test_negative_subtotal_raises():
    with pytest.raises(ValueError):
        cost(sub=-0.01)


def test_zero_subtotal_allowed():
    assert cost(sub=0) == Decimal("8.00")


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_values_raise_value_error(bad):
    with pytest.raises(ValueError):
        cost(wt=bad)
