from decimal import Decimal

import pytest

from solution import shipping_cost


def cost(l=10, w=10, h=10, weight=1, zone=1, subtotal=0):
    return shipping_cost(l, w, h, weight, zone, subtotal)


def test_returns_decimal_with_two_places():
    result = cost()
    assert isinstance(result, Decimal)
    assert result == Decimal("8.00")
    assert result.as_tuple().exponent == -2


def test_one_kg_or_half_kg_costs_8():
    assert cost(weight=0.5) == Decimal("8.00")
    assert cost(weight=1) == Decimal("8.00")


def test_weight_rounds_up_to_half_kg():
    assert cost(weight=1.0001) == Decimal("9.50")
    assert cost(weight=1.2) == Decimal("9.50")
    assert cost(weight=1.5) == Decimal("9.50")
    assert cost(weight=2) == Decimal("11.00")


def test_float_uses_str_form():
    assert cost(weight=0.1) == Decimal("8.00")
    # 0.1 * 1 * 1 / 5000 is tiny, so the 0.1 kg weight rounds up to 0.5 kg -> 8.00
    assert cost(l=0.1, w=1, h=1, weight=0.1) == Decimal("8.00")
    assert cost(weight=1.5 + 1e-12) == Decimal("11.00")


def test_decimal_inputs_accepted():
    assert cost(weight=Decimal("1.5")) == Decimal("9.50")


def test_volumetric_weight_applies_when_larger():
    # 50*50*50 / 5000 = 25 kg -> 8 + 1.5 * 48 = 80
    assert cost(l=50, w=50, h=50, weight=1) == Decimal("80.00")
    # 10*10*15 / 5000 = 0.3 kg is smaller than 1 kg actual
    assert cost(l=10, w=10, h=15, weight=1) == Decimal("8.00")


def test_zone_factors():
    assert cost(weight=2, zone=1) == Decimal("11.00")
    assert cost(weight=2, zone=2) == Decimal("13.75")
    assert cost(weight=2, zone=3) == Decimal("17.60")


def test_round_half_up_at_end():
    # 9.50 * 1.25 = 11.875 -> 11.88
    assert cost(weight=1.5, zone=2) == Decimal("11.88")


def test_free_shipping_zone_1_and_2_at_150():
    assert cost(weight=2, zone=1, subtotal=150) == Decimal("0.00")
    assert cost(weight=2, zone=2, subtotal=500) == Decimal("0.00")
    assert cost(weight=2, zone=1, subtotal=149.99) == Decimal("11.00")


def test_no_free_shipping_zone_3():
    assert cost(weight=2, zone=3, subtotal=500) == Decimal("17.60")


def test_oversize_surcharge_added_unmultiplied():
    assert cost(l=121, w=1, h=1, weight=1, zone=1) == Decimal("20.00")
    assert cost(l=121, w=1, h=1, weight=2, zone=3) == Decimal("29.60")


def test_oversize_not_waived_by_free_shipping():
    assert cost(l=121, w=1, h=1, weight=1, zone=1, subtotal=200) == Decimal("12.00")


def test_exactly_120_is_not_oversize():
    assert cost(l=120, w=1, h=1, weight=1) == Decimal("8.00")


@pytest.mark.parametrize("bad", [True, False, "1", None, [1]])
def test_non_number_raises_type_error_for_dimension(bad):
    with pytest.raises(TypeError):
        cost(l=bad)


def test_bool_weight_raises_type_error():
    with pytest.raises(TypeError):
        cost(weight=True)


def test_bool_subtotal_raises_type_error():
    with pytest.raises(TypeError):
        cost(subtotal=True)


@pytest.mark.parametrize("kwargs", [
    {"l": 0}, {"w": -1}, {"h": 0}, {"weight": 0}, {"weight": -2},
    {"subtotal": -0.01},
])
def test_non_positive_values_raise_value_error(kwargs):
    with pytest.raises(ValueError):
        cost(**kwargs)


@pytest.mark.parametrize("zone", [True, 0, 4, 1.0, "1", None])
def test_invalid_zone_raises_value_error(zone):
    with pytest.raises(ValueError):
        cost(zone=zone)


def test_non_finite_raises_value_error():
    with pytest.raises(ValueError):
        cost(weight=float("nan"))
    with pytest.raises(ValueError):
        cost(subtotal=float("inf"))
