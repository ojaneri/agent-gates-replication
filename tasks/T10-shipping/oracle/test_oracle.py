from decimal import Decimal

import pytest

from solution import shipping_cost


def c(*args):
    return shipping_cost(*args)


@pytest.mark.parametrize("args,expected", [
    ((10, 10, 10, 0.4, 1, 0), "8.00"),          # billable 0.5
    ((10, 10, 10, 1, 1, 0), "8.00"),            # exactly 1 kg
    ((10, 10, 10, 1.01, 1, 0), "9.50"),         # rounds up to 1.5
    ((10, 10, 10, 1.2, 1, 0), "9.50"),          # rounds up, not to nearest
    ((10, 10, 10, 2, 1, 0), "11.00"),
    ((10, 10, 10, 2.5, 1, 0), "12.50"),
    ((50, 40, 30, 2, 1, 0), "41.00"),           # volumetric 12 kg dominates
    ((50, 40, 31, 2, 1, 0), "42.50"),           # volumetric 12.4 -> 12.5
    ((10, 10, 10, 2.5, 2, 0), "15.63"),         # 12.50 * 1.25 = 15.625, HALF_UP
    ((10, 10, 10, 1.5, 3, 0), "15.20"),         # 9.50 * 1.6
    ((10, 10, 10, 1, 2, 0), "10.00"),
    ((10, 10, 10, 1, 3, 0), "12.80"),
    ((10, 10, 10, 1, 1, 150), "0.00"),          # free at exactly 150
    ((10, 10, 10, 1, 2, 150), "0.00"),
    ((10, 10, 10, 1, 1, 149.99), "8.00"),
    ((10, 10, 10, 1, 3, 200), "12.80"),         # no free shipping in zone 3
    ((121, 10, 10, 1, 3, 0), "32.00"),          # 12.50 * 1.6 + 12.00
    ((10, 121, 10, 1, 1, 0), "24.50"),          # any side counts
    ((10, 10, 121, 1, 1, 0), "24.50"),
    ((120, 10, 10, 1, 1, 0), "12.50"),          # exactly 120 is not oversize
    ((130, 10, 10, 1, 1, 150), "12.00"),        # surcharge survives free shipping
    ((Decimal("10"), 10.0, 10, Decimal("0.5"), 1, Decimal("0")), "8.00"),
    ((1, 1, 1, 1, 1, 0), "8.00"),                # small but valid dimensions
    ((0.5, 0.5, 0.5, 0.1, 1, 0), "8.00"),
])
def test_cost(args, expected):
    r = c(*args)
    assert isinstance(r, Decimal)
    assert str(r) == expected


@pytest.mark.parametrize("args", [
    (0, 10, 10, 1, 1, 0), (10, 0, 10, 1, 1, 0), (10, 10, 0, 1, 1, 0), (10, 10, -1, 1, 1, 0),
    (10, 10, 10, 0, 1, 0), (10, 10, 10, -1, 1, 0), (10, 10, 10, 1, 1, -0.01),
    (10, 10, 10, 1, 0, 0), (10, 10, 10, 1, 4, 0), (10, 10, 10, 1, True, 0), (10, 10, 10, 1, 1.0, 0),
    (10, 10, 10, 1, "1", 0),
])
def test_value_errors(args):
    with pytest.raises(ValueError):
        c(*args)


@pytest.mark.parametrize("args", [
    ("10", 10, 10, 1, 1, 0), (10, 10, 10, "1", 1, 0), (10, 10, 10, 1, 1, None), (True, 10, 10, 1, 1, 0),
    (10, 10, 10, False, 1, 0),
])
def test_type_errors(args):
    with pytest.raises(TypeError):
        c(*args)


@pytest.mark.parametrize("args", [
    (float("nan"), 10, 10, 1, 1, 0), (10, 10, 10, float("nan"), 1, 0), (10, 10, 10, 1, 1, Decimal("NaN")),
])
def test_nan_is_not_positive(args):
    # added after the extension run (deviations.md, fifth correction): NaN is not greater than zero
    with pytest.raises(ValueError):
        c(*args)
